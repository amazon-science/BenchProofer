# P2 adversarial audit — pydata__xarray-6461

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

Counterexample / evidence:

```
Weak candidate patch (keep_attrs = lambda attrs, context: attrs[1] if len(attrs) > 1 else {}) is REJECTED by probe_4: xr.where(cond_with_attrs, 5, y_with_attrs, keep_attrs=True) returns attrs {'attr':'y'} instead of the required {} because when x is scalar the fixed positional index [1] into the labelled-inputs attr list points at y, not x. This violates Requirement 1.3 (scalar x -> attrs must remain {} regardless of cond/y attrs). The gold fix resolves attrs directly from getattr(x,'attrs',{}), which is index-independent.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
import xarray as xr

# Positive control: Req1.1 + Req1.2
# scalar x with keep_attrs=True must return a result (no IndexError) and attrs == {}
cond = xr.DataArray([1, 2, 3], dims="x") > 0
try:
    actual = xr.where(cond, 1, 0, keep_attrs=True)
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    sys.exit(1)
print("returned:", actual.values.tolist(), "attrs:", dict(actual.attrs))
if dict(actual.attrs) != {}:
    print("FAIL: attrs not empty")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
import xarray as xr

# Req2.1: labelled x -> result.attrs == x's own attrs
cond = xr.DataArray([True, False], dims="x")
x = xr.DataArray([1, 1], dims="x", attrs={"attr": "x"})
y = xr.DataArray([0, 0], dims="x", attrs={"attr": "y"})
actual = xr.where(cond, x, y, keep_attrs=True)
print("result attrs:", dict(actual.attrs))
if dict(actual.attrs) != {"attr": "x"}:
    print("FAIL: expected {'attr':'x'}")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
import xarray as xr

# Req2.2: cond, x, y all labelled with distinct attrs -> result attrs from x, not cond/y
cond = xr.DataArray([True, False], dims="x", attrs={"attr": "cond"})
x = xr.DataArray([1, 1], dims="x", attrs={"attr": "x"})
y = xr.DataArray([0, 0], dims="x", attrs={"attr": "y"})
actual = xr.where(cond, x, y, keep_attrs=True)
print("result attrs:", dict(actual.attrs))
if dict(actual.attrs) != {"attr": "x"}:
    print("FAIL: expected x's attrs, got", dict(actual.attrs))
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
import xarray as xr

# Req1.3: x scalar, but cond and y carry attrs -> result attrs stays {} (not influenced by cond/y)
cond = xr.DataArray([True, False], dims="x", attrs={"attr": "cond"})
y = xr.DataArray([0, 0], dims="x", attrs={"attr": "y"})
actual = xr.where(cond, 5, y, keep_attrs=True)
print("result:", actual.values.tolist(), "attrs:", dict(actual.attrs))
if dict(actual.attrs) != {}:
    print("FAIL: expected empty attrs, got", dict(actual.attrs))
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
import xarray as xr

# Req3.2: keep_attrs=False -> empty attrs regardless of inputs
cond = xr.DataArray([True, False], dims="x", attrs={"attr": "cond"})
x = xr.DataArray([1, 1], dims="x", attrs={"attr": "x"})
y = xr.DataArray([0, 0], dims="x", attrs={"attr": "y"})
actual = xr.where(cond, x, y, keep_attrs=False)
print("keep_attrs=False result attrs:", dict(actual.attrs))
if dict(actual.attrs) != {}:
    print("FAIL: expected empty attrs")
    sys.exit(1)
# Req3.1: default (None) -> global default False -> empty attrs
actual2 = xr.where(cond, x, y)
print("default result attrs:", dict(actual2.attrs))
if dict(actual2.attrs) != {}:
    print("FAIL: default expected empty attrs")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
import xarray as xr
import numpy as np

# Req4.1/4.2/4.3: value-selection & broadcasting unchanged; scalar x preserves selection semantics
cond = xr.DataArray([True, False, True], dims="x")
# labelled arrays
x = xr.DataArray([10, 20, 30], dims="x")
y = xr.DataArray([-1, -2, -3], dims="x")
r = xr.where(cond, x, y)
print("array select:", r.values.tolist())
if r.values.tolist() != [10, -2, 30]:
    print("FAIL: selection wrong")
    sys.exit(1)

# scalar branches with keep_attrs=True (the fixed path) must still select correctly
r2 = xr.where(cond, 1, 0, keep_attrs=True)
print("scalar select:", r2.values.tolist())
if r2.values.tolist() != [1, 0, 1]:
    print("FAIL: scalar selection wrong")
    sys.exit(1)

# richest type: Dataset -> Dataset
ds = xr.Dataset({"a": ("x", [1, 2, 3])})
r3 = xr.where(cond, ds, 0)
print("type with dataset:", type(r3).__name__)
if not isinstance(r3, xr.Dataset):
    print("FAIL: expected Dataset result type")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
import xarray as xr

# Positive control: Req1.1 + Req1.2
# scalar x with keep_attrs=True must return a result (no IndexError) and attrs == {}
cond = xr.DataArray([1, 2, 3], dims="x") > 0
try:
    actual = xr.where(cond, 1, 0, keep_attrs=True)
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    sys.exit(1)
print("returned:", actual.values.tolist(), "attrs:", dict(actual.attrs))
if dict(actual.attrs) != {}:
    print("FAIL: attrs not empty")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree. Coverage: probe_1 Req1.1+1.2 (scalar x: no IndexError, attrs=={}) — also the positive control (FAILS at base with IndexError, HOLDS patched, discriminating power confirmed by runner via --base). probe_2 Req2.1 (labelled x -> x's attrs). probe_3 Req2.2 (cond/x/y all labelled distinct -> x's attrs, not cond/y). probe_4 Req1.3 (scalar x with cond/y carrying attrs -> stays {}). probe_5 Req3.1+3.2 (keep_attrs=False and default None -> {}). probe_6 Req4.1/4.2/4.3 (value selection, scalar broadcasting, richest-type Dataset result). Candidate-patch exercise: >=1 exercised, >=1 REJECTED (index_with_length_guard rejected by probe_4). No requirements-conforming alternative found that would fail hidden tests; the suite's Req1.3 probe closes the positional-index loophole a weak reading permits. VIOLATION direction: no probe fails on patched tree. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate patch (keep_attrs = lambda attrs, context: attrs[1] if len(attrs) > 1 else {}) is REJECTED by probe_4: xr.where(cond_with_attrs, 5, y_with_attrs, keep_attrs=True) returns attrs {'attr':'y'} instead of the required {} because when x is scalar the fixed positional index [1] into the labelled-inputs attr list points at y, not x. This violates Requirement 1.3 (scalar x -> attrs must remain {} regardless of cond/y attrs). The gold fix resolves attrs directly from getattr(x,'attrs',{}), which is index-independent.
```

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
import sys
import xarray as xr

# Positive control: Req1.1 + Req1.2
# scalar x with keep_attrs=True must return a result (no IndexError) and attrs == {}
cond = xr.DataArray([1, 2, 3], dims="x") > 0
try:
    actual = xr.where(cond, 1, 0, keep_attrs=True)
except Exception as e:
    print("FAIL: raised", type(e).__name__, e)
    sys.exit(1)
print("returned:", actual.values.tolist(), "attrs:", dict(actual.attrs))
if dict(actual.attrs) != {}:
    print("FAIL: attrs not empty")
    sys.exit(1)
print("PASS")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree. Coverage: probe_1 Req1.1+1.2 (scalar x: no IndexError, attrs=={}) — also the positive control (FAILS at base with IndexError, HOLDS patched, discriminating power confirmed by runner via --base). probe_2 Req2.1 (labelled x -> x's attrs). probe_3 Req2.2 (cond/x/y all labelled distinct -> x's attrs, not cond/y). probe_4 Req1.3 (scalar x with cond/y carrying attrs -> stays {}). probe_5 Req3.1+3.2 (keep_attrs=False and default None -> {}). probe_6 Req4.1/4.2/4.3 (value selection, scalar broadcasting, richest-type Dataset result). Candidate-patch exercise: >=1 exercised, >=1 REJECTED (index_with_length_guard rejected by probe_4). No requirements-conforming alternative found that would fail hidden tests; the suite's Req1.3 probe closes the positional-index loophole a weak reading permits. VIOLATION direction: no probe fails on patched tree. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the changed observable behavior (attrs resolved from x directly), not a narrow slice or one branch. R1.3's claim that y/cond attrs never leak into the result is verified live. R3.1 (keep_attrs=None -> global option default False) is consistent with unchanged surrounding code. No mandated behavior the patched code lacks, no forbidden behavior it exhibits, no invented behavior. Base probe confirms the exact IndexError described in the issue/Requirement 1.1.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes behavior using only the public function signature (where(cond, x, y, keep_attrs)) and the module path xarray/core/computation.py — both legitimate localization. The core defect (IndexError on scalar second arg under keep_attrs=True, and keeping x's attributes) is fully disclosed in the public problem_statement. No hidden-test content leaks: no test function/class names (test_where_attrs), no file path (xarray/tests/test_computation.py), no parametrization ids, no quoted test code. The gold fix `getattr(x, "attrs", {})` is expressed only as behavioral prose ('resolve preserved attributes directly from x's own attribute mapping, empty when x is a scalar'), inventing no identifiers. Requirement 1.2's 'returned .attrs SHALL be {} for scalar x' is a behavioral consequence of the fix, not a transmitted assertion; Requirement 2 (keep x's attrs, not cond/y) restates documented behavior. Case enumerations track behavior (scalar vs labelled, keep_attrs None/True/False) rather than mirroring test parametrization (the F2P test is unparametrized, just adds one scalar assertion).


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
