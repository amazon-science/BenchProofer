# P2 adversarial audit — pytest-dev__pytest-6202

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
# Positive control: Req2.3 / Req1.3 — parametrization id containing ".[" must be
# preserved. id "..[" -> item name "test_boo[..[]" and getmodpath "test_boo[..[]".
# At base the ".["->"[" rewrite drops a char, giving "...[.[]" style corruption.
import sys, os, tempfile, textwrap
import pytest

SRC = textwrap.dedent('''
    import pytest
    @pytest.mark.parametrize("a", ["..["])
    def test_boo(a):
        pass
''')

class Collector:
    def __init__(self): self.items = []
    def pytest_itemcollected(self, item): self.items.append(item)

def main():
    d = tempfile.mkdtemp()
    f = os.path.join(d, "bug.py")
    open(f, "w").write(SRC)
    col = Collector()
    rc = pytest.main(["--collect-only", "-p", "no:cacheprovider", "-q", f], plugins=[col])
    assert col.items, "no items collected"
    it = col.items[0]
    name = it.name
    modpath = it.getmodpath()
    print("collect rc:", rc)
    print("item.name =", repr(name))
    print("getmodpath =", repr(modpath))
    exp_name = "test_boo[..[]"
    exp_modpath = "test_boo[..[]"
    ok = name == exp_name and modpath == exp_modpath
    print("expected name/modpath =", repr(exp_name), repr(exp_modpath))
    if not ok:
        print("MISMATCH: id '.' before '[' was corrupted/dropped")
        sys.exit(1)
    print("OK: ..[ id preserved verbatim")
    sys.exit(0)

main()
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys, os, tempfile, textwrap
import pytest
class _Col:
    def __init__(self): self.items = []
    def pytest_itemcollected(self, item): self.items.append(item)
def collect(src, fname="mod_under_test.py"):
    d = tempfile.mkdtemp(); f = os.path.join(d, fname)
    open(f, "w").write(textwrap.dedent(src))
    col = _Col()
    pytest.main(["--collect-only", "-p", "no:cacheprovider", "-q", f], plugins=[col])
    return col.items, f

items, f = collect('''
    def testone():
        pass
    class TestX(object):
        def testmethod_one(self):
            pass
''')
byname = {it.name: it for it in items}
print("names:", sorted(byname))
assert "testone" in byname, "missing testone"
assert "testmethod_one" in byname, "missing testmethod_one"
mp_fn = byname["testone"].getmodpath()
mp_m = byname["testmethod_one"].getmodpath()
print("testone getmodpath =", repr(mp_fn))
print("testmethod_one getmodpath =", repr(mp_m))
ok = mp_fn == "testone" and mp_m == "TestX.testmethod_one"
if not ok:
    print("MISMATCH: expected 'testone' and 'TestX.testmethod_one'"); sys.exit(1)
print("OK"); sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys, os, tempfile, textwrap
import pytest
class _Col:
    def __init__(self): self.items = []
    def pytest_itemcollected(self, item): self.items.append(item)
def collect(src, fname="mod_under_test.py"):
    d = tempfile.mkdtemp(); f = os.path.join(d, fname)
    open(f, "w").write(textwrap.dedent(src))
    col = _Col()
    pytest.main(["--collect-only", "-p", "no:cacheprovider", "-q", f], plugins=[col])
    return col.items, f

items, f = collect('''
    import pytest
    @pytest.mark.parametrize("x", ["a.b", "plain"])
    def test_p(x):
        pass
''')
names = sorted(it.name for it in items)
mps = sorted(it.getmodpath() for it in items)
print("names:", names)
print("modpaths:", mps)
exp_names = ["test_p[a.b]", "test_p[plain]"]
exp_mps = ["test_p[a.b]", "test_p[plain]"]
if names != exp_names or mps != exp_mps:
    print("MISMATCH: expected", exp_names, exp_mps); sys.exit(1)
print("OK: exact join, ids verbatim"); sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys, os, tempfile, textwrap
import pytest
class _Col:
    def __init__(self): self.items = []
    def pytest_itemcollected(self, item): self.items.append(item)
def collect(src, fname="mod_under_test.py"):
    d = tempfile.mkdtemp(); f = os.path.join(d, fname)
    open(f, "w").write(textwrap.dedent(src))
    col = _Col()
    pytest.main(["--collect-only", "-p", "no:cacheprovider", "-q", f], plugins=[col])
    return col.items, f

items, f = collect('''
    def testone():
        pass
''', fname="mymodx.py")
it = items[0]
s = it.getmodpath(stopatmodule=False)
print("getmodpath(stopatmodule=False) =", repr(s))
if not s.endswith("mymodx.testone"):
    print("MISMATCH: expected to end with 'mymodx.testone'"); sys.exit(1)
# default should NOT include module
s2 = it.getmodpath()
print("default getmodpath =", repr(s2))
if s2 != "testone":
    print("MISMATCH: default should be bare 'testone'"); sys.exit(1)
print("OK"); sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys, os, tempfile, textwrap
import pytest
class _Col:
    def __init__(self): self.items = []
    def pytest_itemcollected(self, item): self.items.append(item)
def collect(src, fname="mod_under_test.py"):
    d = tempfile.mkdtemp(); f = os.path.join(d, fname)
    open(f, "w").write(textwrap.dedent(src))
    col = _Col()
    pytest.main(["--collect-only", "-p", "no:cacheprovider", "-q", f], plugins=[col])
    return col.items, f

items, f = collect('''
    import pytest
    def testone():
        pass
    class TestX(object):
        def testmethod_one(self):
            pass
    class TestY(TestX):
        @pytest.mark.parametrize("arg0", [".["])
        def testmethod_two(self, arg0):
            pass
''')
print("count:", len(items))
names = [it.name for it in items]
mps = [it.getmodpath() for it in items]
print("names:", names)
print("modpaths:", mps)
if len(items) != 4:
    print("MISMATCH: expected 4 items"); sys.exit(1)
# TestY inherits testmethod_one -> should report TestY.testmethod_one
if "TestY.testmethod_one" not in mps:
    print("MISMATCH: inherited method should report subclass TestY"); sys.exit(1)
# parametrized ".[" -> name testmethod_two[.[] and modpath TestY.testmethod_two[.[]
if "testmethod_two[.[]" not in names:
    print("MISMATCH: param name testmethod_two[.[] missing; got", names); sys.exit(1)
if "TestY.testmethod_two[.[]" not in mps:
    print("MISMATCH: expected TestY.testmethod_two[.[] modpath; got", mps); sys.exit(1)
# also TestX.testmethod_one present (base collection)
if "TestX.testmethod_one" not in mps:
    print("MISMATCH: TestX.testmethod_one missing"); sys.exit(1)
print("OK: full scenario matches"); sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys, os, tempfile, textwrap
import pytest
class _Col:
    def __init__(self): self.items = []
    def pytest_itemcollected(self, item): self.items.append(item)
def collect(src, fname="mod_under_test.py"):
    d = tempfile.mkdtemp(); f = os.path.join(d, fname)
    open(f, "w").write(textwrap.dedent(src))
    col = _Col()
    pytest.main(["--collect-only", "-p", "no:cacheprovider", "-q", f], plugins=[col])
    return col.items, f

items, f = collect('''
    class TestZ(object):
        def test_m(self):
            pass
''')
it = items[0]
mp = it.getmodpath()
print("getmodpath =", repr(mp))
parts = mp.split(".")
print("parts:", parts)
if mp != "TestZ.test_m" or len(parts) != 2:
    print("MISMATCH: expected exactly 'TestZ.test_m' with no wrapper segment"); sys.exit(1)
print("OK: no wrapper node in path"); sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: Req2.3 / Req1.3 — parametrization id containing ".[" must be
# preserved. id "..[" -> item name "test_boo[..[]" and getmodpath "test_boo[..[]".
# At base the ".["->"[" rewrite drops a char, giving "...[.[]" style corruption.
import sys, os, tempfile, textwrap
import pytest

SRC = textwrap.dedent('''
    import pytest
    @pytest.mark.parametrize("a", ["..["])
    def test_boo(a):
        pass
''')

class Collector:
    def __init__(self): self.items = []
    def pytest_itemcollected(self, item): self.items.append(item)

def main():
    d = tempfile.mkdtemp()
    f = os.path.join(d, "bug.py")
    open(f, "w").write(SRC)
    col = Collector()
    rc = pytest.main(["--collect-only", "-p", "no:cacheprovider", "-q", f], plugins=[col])
    assert col.items, "no items collected"
    it = col.items[0]
    name = it.name
    modpath = it.getmodpath()
    print("collect rc:", rc)
    print("item.name =", repr(name))
    print("getmodpath =", repr(modpath))
    exp_name = "test_boo[..[]"
    exp_modpath = "test_boo[..[]"
    ok = name == exp_name and modpath == exp_modpath
    print("expected name/modpath =", repr(exp_name), repr(exp_modpath))
    if not ok:
        print("MISMATCH: id '.' before '[' was corrupted/dropped")
        sys.exit(1)
    print("OK: ..[ id preserved verbatim")
    sys.exit(0)

main()
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-6202: gold removes the unconditional `s.replace('.[', '[')` in PyobjMixin.getmodpath so parametrization ids containing '.[' survive verbatim.

Probes (all run in the official image; each standalone, stdlib+pytest-repo only, collecting real Item objects via pytest.main --collect-only):
- probe_1 (POSITIVE CONTROL) — Req2.3/1.3: id '..[' => item.name 'test_boo[..[]' AND getmodpath 'test_boo[..[]'. HOLDS patched; VIOLATED at base (base gives 'test_boo[.[]', a dropped char). Discriminates.
- probe_2 — Req1.4/4.1: single scope name returned bare ('testone'); class method => 'TestX.testmethod_one'. HOLDS patched.
- probe_3 — Req1.1/1.2: exact '.'-join, ids 'a.b' and 'plain' preserved verbatim in name and getmodpath. HOLDS patched.
- probe_4 — Req3.3/3.4: default getmodpath omits module ('testone'); stopatmodule=False includes module as outermost segment (ends 'mymodx.testone'). HOLDS patched.
- probe_5 — Req3.5/4.3: full F2P scenario, 4 items, inherited method via subclass => 'TestY.testmethod_one', parametrized '.[' => name 'testmethod_two[.[]' and getmodpath 'TestY.testmethod_two[.[]'. HOLDS patched.
- probe_6 — Req3.2: class method path is exactly 'TestZ.test_m' with no intervening instance-wrapper segment (2 dotted parts). HOLDS patched.

CANDIDATE PATCH (weak.diff): 'lazy' partial fix `s.replace('.[', '[', 1)` — a weak reading that only stops the *first* rewrite. REJECTED by the suite: probe_1 fails ('..[' still corrupted to '.[' since the leading '.[' from the id itself is the first match) and probe_5 fails (id '.[' => getmodpath 'TestY.testmethod_two[[]', wrong). This demonstrates the suite discriminates wrong implementations; no probe-conforming alternative found.

All 6 probes HOLD on the gold-patched tree; positive control FAILS at base (prepatch reproduced). Verdict SOUND.

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
# Positive control: Req2.3 / Req1.3 — parametrization id containing ".[" must be
# preserved. id "..[" -> item name "test_boo[..[]" and getmodpath "test_boo[..[]".
# At base the ".["->"[" rewrite drops a char, giving "...[.[]" style corruption.
import sys, os, tempfile, textwrap
import pytest

SRC = textwrap.dedent('''
    import pytest
    @pytest.mark.parametrize("a", ["..["])
    def test_boo(a):
        pass
''')

class Collector:
    def __init__(self): self.items = []
    def pytest_itemcollected(self, item): self.items.append(item)

def main():
    d = tempfile.mkdtemp()
    f = os.path.join(d, "bug.py")
    open(f, "w").write(SRC)
    col = Collector()
    rc = pytest.main(["--collect-only", "-p", "no:cacheprovider", "-q", f], plugins=[col])
    assert col.items, "no items collected"
    it = col.items[0]
    name = it.name
    modpath = it.getmodpath()
    print("collect rc:", rc)
    print("item.name =", repr(name))
    print("getmodpath =", repr(modpath))
    exp_name = "test_boo[..[]"
    exp_modpath = "test_boo[..[]"
    ok = name == exp_name and modpath == exp_modpath
    print("expected name/modpath =", repr(exp_name), repr(exp_modpath))
    if not ok:
        print("MISMATCH: id '.' before '[' was corrupted/dropped")
        sys.exit(1)
    print("OK: ..[ id preserved verbatim")
    sys.exit(0)

main()
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-6202: gold removes the unconditional `s.replace('.[', '[')` in PyobjMixin.getmodpath so parametrization ids containing '.[' survive verbatim.

Probes (all run in the official image; each standalone, stdlib+pytest-repo only, collecting real Item objects via pytest.main --collect-only):
- probe_1 (POSITIVE CONTROL) — Req2.3/1.3: id '..[' => item.name 'test_boo[..[]' AND getmodpath 'test_boo[..[]'. HOLDS patched; VIOLATED at base (base gives 'test_boo[.[]', a dropped char). Discriminates.
- probe_2 — Req1.4/4.1: single scope name returned bare ('testone'); class method => 'TestX.testmethod_one'. HOLDS patched.
- probe_3 — Req1.1/1.2: exact '.'-join, ids 'a.b' and 'plain' preserved verbatim in name and getmodpath. HOLDS patched.
- probe_4 — Req3.3/3.4: default getmodpath omits module ('testone'); stopatmodule=False includes module as outermost segment (ends 'mymodx.testone'). HOLDS patched.
- probe_5 — Req3.5/4.3: full F2P scenario, 4 items, inherited method via subclass => 'TestY.testmethod_one', parametrized '.[' => name 'testmethod_two[.[]' and getmodpath 'TestY.testmethod_two[.[]'. HOLDS patched.
- probe_6 — Req3.2: class method path is exactly 'TestZ.test_m' with no intervening instance-wrapper segment (2 dotted parts). HOLDS patched.

CANDIDATE PATCH (weak.diff): 'lazy' partial fix `s.replace('.[', '[', 1)` — a weak reading that only stops the *first* rewrite. REJECTED by the suite: probe_1 fails ('..[' still corrupted to '.[' since the leading '.[' from the id itself is the first match) and probe_5 fails (id '.[' => getmodpath 'TestY.testmethod_two[[]', wrong). This demonstrates the suite discriminates wrong implementations; no probe-conforming alternative found.

All 6 probes HOLD on the gold-patched tree; positive control FAILS at base (prepatch reproduced). Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a one-line change in src/_pytest/python.py PyobjMixin.getmodpath: `s=`.`.join(parts); return s.replace('.[','[')` → `return '.'.join(parts)`. The requirements correctly pin the CHANGED observable behavior (exact-join of scope names, verbatim preservation of the `.[` sequence) rather than a helper/branch slice. Confirmed via nl_attack probe on both patched and --base trees: base yields modpath 'test_boo[.[]' (char dropped), patched yields 'test_boo[..[]'. Requirement 3.4 (stopatmodule=False) and 3.2/3.5 (wrapper skip, subclass) describe pre-existing behavior that the patch preserves — consistent with Requirement 4 (change only the erroneous rewrite); all verified present in patched code.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes only public/behavioral content. The core defect (`.[`→`[` rewrite in getmodpath, module src/_pytest/python.py, consumed via reportinfo and reports.py headline construction) and the example ids `..[`/`.[` all come from the public problem_statement. Naming getmodpath/PyobjMixin/reportinfo/reports.py is legitimate localization. The document does NOT transmit any hidden-test artifacts: no test file path (testing/test_collection.py), no test/class names (Test_genitems::test_example_items1, TestX, TestY, testmethod_one/two, testone), no parametrization ids reproduced as such, no verbatim gold-patch lines, and no fix-invented identifiers (the gold merely deletes `return s.replace(".[", "[")`). Req 3 AC4 (stopatmodule=False includes module name) and AC5 (base-class method collected through subclass reports subclass name) mirror hidden-test scenarios but are expressed as generic behavioral requirements of the documented getmodpath API using placeholders (<ClassName>.<methodName>), i.e. translating what the tests check into behavior — the intended activity — rather than reconstructing the tests. No case enumeration mirrors the test parametrization. NO-LEAKAGE.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
