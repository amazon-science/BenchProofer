# P2 adversarial audit — astropy__astropy-7336

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
Weak candidate (guard `return_ is not None` instead of guarding the annotation) is REJECTED by probe_2: with `-> None` annotation and the function returning a real Quantity (5*u.m), the wrapper still calls `.to(None)` and raises `TypeError: None is not a valid Unit`. Requirement 1.3 mandates no unit-conversion operation on the returned value when the annotation is None, regardless of the value. The gold patch (guard the annotation) satisfies this; the naive value-guard does not.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control: Requirement 1.2 / 1.1 / 1.3
A callable annotated `-> None` returns its value unchanged with no exception.
On base this raises AttributeError ('NoneType' has no attribute 'to').
"""
import sys
from astropy import units as u


@u.quantity_input
def myfunc(x: u.arcsec) -> None:
    return None


try:
    result = myfunc(1 * u.arcsec)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)

print("returned:", repr(result))
if result is not None:
    print("expected None, got", repr(result))
    sys.exit(1)
print("OK: -> None annotation returned value unchanged, no exception")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 1.1 / 1.3: `None` return annotation => value returned UNCHANGED,
no conversion attempted, even when the returned value IS a Quantity.
This discriminates against a weak fix that only guards `return_ is None`
instead of guarding the annotation.
"""
import sys
from astropy import units as u


@u.quantity_input
def myfunc(x: u.arcsec) -> None:
    # returns a real quantity in a different unit; must NOT be converted
    return 5 * u.m


try:
    result = myfunc(1 * u.arcsec)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)

print("returned:", repr(result))
# Must be returned unchanged: still 5 m, not converted to None or anything else
if not (result.value == 5 and result.unit == u.m):
    print("value/unit changed unexpectedly")
    sys.exit(1)
print("OK: None annotation returned quantity unchanged")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 2.1 / 2.2: concrete-unit return annotation still converts result.
"""
import sys
from astropy import units as u


@u.quantity_input
def myfunc(x: u.arcsec) -> u.deg:
    return x


result = myfunc(3600 * u.arcsec)
print("returned:", repr(result))
if result.unit != u.deg:
    print("unit not converted to deg:", result.unit)
    sys.exit(1)
import numpy as np
if not np.isclose(result.value, 1.0):
    print("value wrong:", result.value)
    sys.exit(1)
print("OK: concrete return annotation converts result to deg")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 2.3: no return annotation => result unchanged.
Requirement 3.1: argument passed through preserving its original unit.
"""
import sys
from astropy import units as u


@u.quantity_input
def myfunc(x: u.arcsec):
    return x


result = myfunc(1 * u.arcsec)
print("returned:", repr(result))
# no return annotation -> unchanged, arg unit preserved (not force-converted)
if result.unit != u.arcsec or result.value != 1:
    print("arg unit not preserved / result changed:", result)
    sys.exit(1)
print("OK: no return annotation returns unchanged, arg unit preserved")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 4.1 / 4.2: non-convertible argument raises UnitsError with message.
Requirement 4.3: value with no unit attribute raises TypeError.
"""
import sys
from astropy import units as u


@u.quantity_input
def myfunc(x: u.arcsec):
    return x


ok = True

# 4.1/4.2 non-convertible
try:
    myfunc(1 * u.kg)
    print("FAIL: no error for non-convertible unit")
    ok = False
except u.UnitsError as e:
    print("UnitsError:", e)
except Exception as e:
    print("FAIL: wrong exception type:", type(e).__name__, e)
    ok = False

# 4.3 plain number -> TypeError mentioning unit attribute
try:
    myfunc(5)
    print("FAIL: no error for plain number")
    ok = False
except TypeError as e:
    print("TypeError:", e)
    if "unit" not in str(e).lower():
        print("FAIL: TypeError message doesn't mention 'unit'")
        ok = False
except Exception as e:
    print("FAIL: wrong exception type for plain number:", type(e).__name__, e)
    ok = False

if not ok:
    sys.exit(1)
print("OK: error behavior preserved")
sys.exit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Requirement 3.2: decorator keyword target takes precedence over annotation.
Requirement 3.3: equivalencies in force during validation.
Requirement 3.6: physical-type strings accepted.
"""
import sys
from astropy import units as u


# 3.6 physical-type string via annotation
@u.quantity_input
def f_ptype(x: 'angle'):
    return x

r = f_ptype(1 * u.arcsec)
print("ptype string accepted:", repr(r))
if r.unit != u.arcsec:
    print("FAIL ptype")
    sys.exit(1)

# 3.2 decorator keyword target
@u.quantity_input(x=u.arcsec)
def f_kw(x):
    return x

r2 = f_kw(1 * u.deg)  # deg convertible to arcsec (angle) -> accepted
print("kw target accepted:", repr(r2))
# should preserve original unit (deg)
if r2.unit != u.deg:
    print("FAIL: kw target force-converted arg unit:", r2.unit)
    sys.exit(1)

# 3.3 equivalencies
@u.quantity_input(x=u.Hz, equivalencies=u.spectral())
def f_eq(x):
    return x

r3 = f_eq(1 * u.m)  # only convertible under spectral equivalency
print("equivalency accepted:", repr(r3))
if r3.unit != u.m:
    print("FAIL: equivalency arg unit changed:", r3.unit)
    sys.exit(1)

print("OK: 3.2/3.3/3.6 preserved")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control: Requirement 1.2 / 1.1 / 1.3
A callable annotated `-> None` returns its value unchanged with no exception.
On base this raises AttributeError ('NoneType' has no attribute 'to').
"""
import sys
from astropy import units as u


@u.quantity_input
def myfunc(x: u.arcsec) -> None:
    return None


try:
    result = myfunc(1 * u.arcsec)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)

print("returned:", repr(result))
if result is not None:
    print("expected None, got", repr(result))
    sys.exit(1)
print("OK: -> None annotation returned value unchanged, no exception")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

All 6 probes HOLD on the gold-patched tree. Positive control (probe_1: `-> None` returns None with no AttributeError) FAILS at base (AttributeError 'NoneType' object has no attribute 'to') — discriminating power confirmed. Probe_2 also fails at base (TypeError None is not a valid Unit). Coverage: R1.1/1.2/1.3 (probe_1, probe_2), R2.1/2.2 (probe_3), R2.3/3.1 (probe_4), R4.1/4.2/4.3 (probe_5), R3.2/3.3/3.6 (probe_6). Candidate patch exercised (>=1) and REJECTED (>=1) by the suite: the value-guard weak fix passes 5/6 probes but is rejected by probe_2, demonstrating the suite discriminates the annotation-guard requirement (R1.3) from a lazy value-guard. No requirements-conforming wrong fix found; suite is faithful to gold. Verdict: SOUND.

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
Weak candidate (guard `return_ is not None` instead of guarding the annotation) is REJECTED by probe_2: with `-> None` annotation and the function returning a real Quantity (5*u.m), the wrapper still calls `.to(None)` and raises `TypeError: None is not a valid Unit`. Requirement 1.3 mandates no unit-conversion operation on the returned value when the annotation is None, regardless of the value. The gold patch (guard the annotation) satisfies this; the naive value-guard does not.
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
"""Positive control: Requirement 1.2 / 1.1 / 1.3
A callable annotated `-> None` returns its value unchanged with no exception.
On base this raises AttributeError ('NoneType' has no attribute 'to').
"""
import sys
from astropy import units as u


@u.quantity_input
def myfunc(x: u.arcsec) -> None:
    return None


try:
    result = myfunc(1 * u.arcsec)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)

print("returned:", repr(result))
if result is not None:
    print("expected None, got", repr(result))
    sys.exit(1)
print("OK: -> None annotation returned value unchanged, no exception")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

All 6 probes HOLD on the gold-patched tree. Positive control (probe_1: `-> None` returns None with no AttributeError) FAILS at base (AttributeError 'NoneType' object has no attribute 'to') — discriminating power confirmed. Probe_2 also fails at base (TypeError None is not a valid Unit). Coverage: R1.1/1.2/1.3 (probe_1, probe_2), R2.1/2.2 (probe_3), R2.3/3.1 (probe_4), R4.1/4.2/4.3 (probe_5), R3.2/3.3/3.6 (probe_6). Candidate patch exercised (>=1) and REJECTED (>=1) by the suite: the value-guard weak fix passes 5/6 probes but is rejected by probe_2, demonstrating the suite discriminates the annotation-guard requirement (R1.3) from a lazy value-guard. No requirements-conforming wrong fix found; suite is faithful to gold. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed both patched (HOLDS, exit 0) and base (VIOLATED, exit 1 with the exact AttributeError from the issue). Requirements correctly pin the changed behavior biconditionally: None/empty => unchanged, concrete unit => convert. Preserved-behavior requirements (arg validation, error messages, equivalencies, None-permitting targets) are all real astropy quantity_input behaviors, not invented. No forbidden/mandated divergence found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe the None-return-annotation fix (public in problem_statement) and pre-existing quantity_input decorator behavior (arg validation, equivalencies, kwargs/defaults, error types). Reqs 3-4 correspond to PASS_TO_PASS tests but are stated as behavioral requirements, not test artifacts: no test names/paths (test_quantity_annotations.py, test_return_annotation_none), no parametrization ids, no quoted test or gold code, no fix-invented identifiers (the gold edit is a one-line condition change inventing no names). The only borderline items are the verbatim error strings in Req 4.2/4.3 ("must be in units convertible to…" and "has no 'unit' attribute. You may want to pass in an astropy Quantity instead.") which match test assertions, but these are pre-existing source-code error messages in the base commit — legitimate observable behavior to specify, not fix- or test-derived content. The doc does not enumerate the parametrized (u.arcsec/'angle') case pairs, so no test-shaped reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
