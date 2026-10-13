# P2 adversarial audit — pytest-dev__pytest-5631

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_posctrl.py`, `probe_2_sentinel_counted.py`, `probe_3_named_notcounted.py`, `probe_4_explicit_notcounted.py`, `probe_5_empty.py`, `probe_6_mixed.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_posctrl.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1_posctrl.py` → holds on the patched tree (good)

```python
# Req 1.1/1.3 positive control: an array-like replacement with ambiguous __eq__
# must NOT crash num_mock_patch_args; identity comparison => not a sentinel => 0.
import unittest.mock  # ensure sys.modules["unittest.mock"] present
from _pytest.compat import num_mock_patch_args

class AmbiguousBool:
    def __bool__(self):
        raise ValueError("truth value of an array is ambiguous")

class ArrayLike:
    def __eq__(self, other):
        return AmbiguousBool()   # like numpy: == yields array, bool() raises
    __hash__ = None

class Patching:
    def __init__(self, attribute_name, new):
        self.attribute_name = attribute_name
        self.new = new

def f():
    pass
f.patchings = [Patching(None, ArrayLike())]

n = num_mock_patch_args(f)   # must not raise
print("num_mock_patch_args(array-like) =", n)
assert n == 0, "array-like explicit replacement must not be counted"
print("OK: no ambiguous-truth-value error, count == 0")
```

Attack 2 — `probe_2_sentinel_counted.py` → holds on the patched tree (good)

```python
# Req 2.4: no attribute_name + replacement is DEFAULT sentinel => counted.
import unittest.mock
from _pytest.compat import num_mock_patch_args
class Patching:
    def __init__(self, attribute_name, new):
        self.attribute_name = attribute_name; self.new = new
def f(): pass
f.patchings = [Patching(None, unittest.mock.DEFAULT)]
n = num_mock_patch_args(f)
print("count for single DEFAULT patching =", n)
assert n == 1
print("OK")
```

Attack 3 — `probe_3_named_notcounted.py` → holds on the patched tree (good)

```python
# Req 2.2: a patching that binds a named attribute is NOT counted even if new is DEFAULT.
import unittest.mock
from _pytest.compat import num_mock_patch_args
class Patching:
    def __init__(self, attribute_name, new):
        self.attribute_name = attribute_name; self.new = new
def f(): pass
f.patchings = [Patching("some_attr", unittest.mock.DEFAULT)]
n = num_mock_patch_args(f)
print("count for named-attr patching =", n)
assert n == 0
print("OK")
```

Attack 4 — `probe_4_explicit_notcounted.py` → holds on the patched tree (good)

```python
# Req 2.3: explicit non-sentinel replacement (identity differs) is NOT counted.
import unittest.mock
from _pytest.compat import num_mock_patch_args
class Patching:
    def __init__(self, attribute_name, new):
        self.attribute_name = attribute_name; self.new = new
def f(): pass
f.patchings = [Patching(None, object())]  # ordinary explicit replacement
n = num_mock_patch_args(f)
print("count for explicit non-sentinel replacement =", n)
assert n == 0
print("OK")
```

Attack 5 — `probe_5_empty.py` → holds on the patched tree (good)

```python
# Req 2.6: no patchings / empty patchings => 0.
import unittest.mock
from _pytest.compat import num_mock_patch_args
def f(): pass
def g(): pass
g.patchings = []
print("no attr:", num_mock_patch_args(f), " empty list:", num_mock_patch_args(g))
assert num_mock_patch_args(f) == 0
assert num_mock_patch_args(g) == 0
print("OK")
```

Attack 6 — `probe_6_mixed.py` → holds on the patched tree (good)

```python
# Req 1 + 2 combined: mixed patchings, incl. ambiguous array-like, must not raise;
# only the (no-name, DEFAULT) ones are counted.  Expected count = 2.
import unittest.mock
from _pytest.compat import num_mock_patch_args
class AmbiguousBool:
    def __bool__(self): raise ValueError("ambiguous")
class ArrayLike:
    def __eq__(self, other): return AmbiguousBool()
    __hash__ = None
class Patching:
    def __init__(self, attribute_name, new):
        self.attribute_name = attribute_name; self.new = new
D = unittest.mock.DEFAULT
def f(): pass
f.patchings = [
    Patching(None, D),               # counted
    Patching(None, ArrayLike()),     # ambiguous, not counted, must not raise
    Patching("named", D),            # named -> not counted
    Patching(None, D),               # counted
    Patching(None, object()),        # explicit -> not counted
]
n = num_mock_patch_args(f)
print("mixed count =", n)
assert n == 2, n
print("OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_posctrl.py`

```python
# Req 1.1/1.3 positive control: an array-like replacement with ambiguous __eq__
# must NOT crash num_mock_patch_args; identity comparison => not a sentinel => 0.
import unittest.mock  # ensure sys.modules["unittest.mock"] present
from _pytest.compat import num_mock_patch_args

class AmbiguousBool:
    def __bool__(self):
        raise ValueError("truth value of an array is ambiguous")

class ArrayLike:
    def __eq__(self, other):
        return AmbiguousBool()   # like numpy: == yields array, bool() raises
    __hash__ = None

class Patching:
    def __init__(self, attribute_name, new):
        self.attribute_name = attribute_name
        self.new = new

def f():
    pass
f.patchings = [Patching(None, ArrayLike())]

n = num_mock_patch_args(f)   # must not raise
print("num_mock_patch_args(array-like) =", n)
assert n == 0, "array-like explicit replacement must not be counted"
print("OK: no ambiguous-truth-value error, count == 0")
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-5631: num_mock_patch_args must detect the DEFAULT sentinel by IDENTITY (is) rather than equality (in/==), so array-like replacements with ambiguous __eq__ don't raise ValueError during collection.

Probe suite (all standalone, stdlib + _pytest only; run in the official image via nl_attack):
- probe_1_posctrl.py (Req 1.1/1.3, POSITIVE CONTROL): patching with an array-like replacement whose __eq__ returns an object whose __bool__ raises. num_mock_patch_args must NOT raise and must return 0 (identity => not a sentinel). PATCHED: HOLDS (count 0). BASE: VIOLATED. Discriminates.
- probe_2 (Req 2.4): (no attr, DEFAULT) => counted 1. PATCHED HOLDS.
- probe_3 (Req 2.2): named attribute + DEFAULT => not counted (0). PATCHED HOLDS.
- probe_4 (Req 2.3): explicit non-sentinel object() => not counted (0). PATCHED HOLDS.
- probe_5 (Req 2.6): no patchings attr / empty list => 0. PATCHED HOLDS.
- probe_6 (Req 1+2 combined): mixed list incl. ambiguous array-like; must not raise; only (no-name, DEFAULT) counted => 2. PATCHED HOLDS.

All 6 hold on the gold-patched tree; positive control fails at base => prepatch reproduced.

CANDIDATE (weak.diff): a naive fix that wraps the original `p.new in sentinels` comprehension in try/except ValueError and falls back to `len(patchings)`. This satisfies the literal 'SHALL NOT raise' reading (no crash, collection would proceed) but violates Req 1.1 (count must remain correct) and Req 2.3 (explicit array-like must not be counted): it over-counts. Under weak.diff, probe_1 (n=1, expected 0) and probe_6 (n=3, expected 2) REJECT it; probes 2/3/4/5 pass. => suite discriminates wrong implementations. This candidate is NOT requirements-conforming (probes reject it), so it is not a TOO-WEAK finding.

Verdict SOUND: >=5 distinct probes covering behavioral SHALLs, boundaries, and regression 'SHALL keep' criteria all hold on patched; positive control discriminates base vs patched; a plausibly-wrong alternative patch is exercised and REJECTED by the suite.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1_posctrl.py`, `probe_2_sentinel_counted.py`, `probe_3_named_notcounted.py`, `probe_4_explicit_notcounted.py`, `probe_5_empty.py`, `probe_6_mixed.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1_posctrl.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1_posctrl.py` → holds on the patched tree (good)

Attack 2 — `probe_2_sentinel_counted.py` → holds on the patched tree (good)

Attack 3 — `probe_3_named_notcounted.py` → holds on the patched tree (good)

Attack 4 — `probe_4_explicit_notcounted.py` → holds on the patched tree (good)

Attack 5 — `probe_5_empty.py` → holds on the patched tree (good)

Attack 6 — `probe_6_mixed.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1_posctrl.py`

```python
# Req 1.1/1.3 positive control: an array-like replacement with ambiguous __eq__
# must NOT crash num_mock_patch_args; identity comparison => not a sentinel => 0.
import unittest.mock  # ensure sys.modules["unittest.mock"] present
from _pytest.compat import num_mock_patch_args

class AmbiguousBool:
    def __bool__(self):
        raise ValueError("truth value of an array is ambiguous")

class ArrayLike:
    def __eq__(self, other):
        return AmbiguousBool()   # like numpy: == yields array, bool() raises
    __hash__ = None

class Patching:
    def __init__(self, attribute_name, new):
        self.attribute_name = attribute_name
        self.new = new

def f():
    pass
f.patchings = [Patching(None, ArrayLike())]

n = num_mock_patch_args(f)   # must not raise
print("num_mock_patch_args(array-like) =", n)
assert n == 0, "array-like explicit replacement must not be counted"
print("OK: no ambiguous-truth-value error, count == 0")
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-5631: num_mock_patch_args must detect the DEFAULT sentinel by IDENTITY (is) rather than equality (in/==), so array-like replacements with ambiguous __eq__ don't raise ValueError during collection.

Probe suite (all standalone, stdlib + _pytest only; run in the official image via nl_attack):
- probe_1_posctrl.py (Req 1.1/1.3, POSITIVE CONTROL): patching with an array-like replacement whose __eq__ returns an object whose __bool__ raises. num_mock_patch_args must NOT raise and must return 0 (identity => not a sentinel). PATCHED: HOLDS (count 0). BASE: VIOLATED. Discriminates.
- probe_2 (Req 2.4): (no attr, DEFAULT) => counted 1. PATCHED HOLDS.
- probe_3 (Req 2.2): named attribute + DEFAULT => not counted (0). PATCHED HOLDS.
- probe_4 (Req 2.3): explicit non-sentinel object() => not counted (0). PATCHED HOLDS.
- probe_5 (Req 2.6): no patchings attr / empty list => 0. PATCHED HOLDS.
- probe_6 (Req 1+2 combined): mixed list incl. ambiguous array-like; must not raise; only (no-name, DEFAULT) counted => 2. PATCHED HOLDS.

All 6 hold on the gold-patched tree; positive control fails at base => prepatch reproduced.

CANDIDATE (weak.diff): a naive fix that wraps the original `p.new in sentinels` comprehension in try/except ValueError and falls back to `len(patchings)`. This satisfies the literal 'SHALL NOT raise' reading (no crash, collection would proceed) but violates Req 1.1 (count must remain correct) and Req 2.3 (explicit array-like must not be counted): it over-counts. Under weak.diff, probe_1 (n=1, expected 0) and probe_6 (n=3, expected 2) REJECT it; probes 2/3/4/5 pass. => suite discriminates wrong implementations. This candidate is NOT requirements-conforming (probes reject it), so it is not a TOO-WEAK finding.

Verdict SOUND: >=5 distinct probes covering behavioral SHALLs, boundaries, and regression 'SHALL keep' criteria all hold on patched; positive control discriminates base vs patched; a plausibly-wrong alternative patch is exercised and REJECTED by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is a one-function rewrite of num_mock_patch_args in src/_pytest/compat.py: replaces `p.new in sentinels` (==-based membership) with identity checks against mock/unittest.mock DEFAULT sentinels, and drops the old `if any(mock_modules): ... else return len(patchings)` fallback (now uses a private object() sentinel when a module is absent, so absent-module patchings are simply not counted — consistent with requirements which only count recognised DEFAULT objects). Requirements pin the changed observable behavior (identity vs ambiguous equality) at the correct boundary rather than a narrow slice. FAIL_TO_PASS test test_mock_sentinel_check_against_numpy_like exercises exactly R1.2. G-RESOLVE=pass. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** All localizing details in requirements.md (num_mock_patch_args, src/_pytest/compat.py, getfuncargnames, 'p.new in sentinels', DEFAULT sentinels from mock/unittest.mock, numpy-array patch triggering ambiguous-truth-value ValueError during collection) are already present in the PUBLIC problem_statement, including its traceback. The fix-invented identifiers from the gold patch (mock_sentinel, ut_mock_sentinel) do NOT appear. The hidden test's identity — path testing/python/integration.py, class TestMockDecoration, method test_mock_sentinel_check_against_numpy_like, the NumpyLike test-double class, and assertoutcome(passed=1) — is not transmitted. The document generalizes ('any object whose equality does not yield a plain boolean') as behavioral description rather than mirroring the single parametrized test case, and 'identity rather than equality' is the natural behavioral statement of the fix. No case enumeration mirroring test parametrization (only one F2P test). Legitimate behavior translation, no gold/test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
