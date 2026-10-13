# P2 adversarial audit — astropy__astropy-14096

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
"""Positive control — Req 1.3 / 1.2 / 1.4.
A subclass property whose body accesses a missing attribute must raise an
AttributeError that names the *inner* missing attribute ('random_attr'),
NOT the property's own name ('prop').

HOLDS on patched tree; FAILS at base (base fabricates a 'prop' message)."""
import sys
from astropy.coordinates import SkyCoord


class custom_coord(SkyCoord):
    @property
    def prop(self):
        return self.random_attr


c = custom_coord("00h42m30s", "+41d12m00s", frame="icrs")
try:
    c.prop
    print("NO EXCEPTION RAISED — criterion violated")
    sys.exit(1)
except AttributeError as e:
    msg = str(e)
    print("AttributeError message:", repr(msg))
    if "random_attr" in msg:
        print("OK: reports the genuinely missing inner attribute")
        sys.exit(0)
    print("FAIL: message does not mention 'random_attr' (blames the property)")
    sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.4 (negative): the raised message must NOT blame the property name.
Complements probe_1 by explicitly asserting 'prop' is not reported as the
missing attribute name. HOLDS patched, FAILS at base."""
import sys
from astropy.coordinates import SkyCoord


class custom_coord(SkyCoord):
    @property
    def prop(self):
        return self.random_attr


c = custom_coord("00h42m30s", "+41d12m00s", frame="icrs")
try:
    c.prop
    print("NO EXCEPTION — violated")
    sys.exit(1)
except AttributeError as e:
    msg = str(e)
    print("message:", repr(msg))
    # Must not fabricate a message reporting 'prop' as the missing attr.
    if "'prop'" in msg or "attribute 'prop'" in msg:
        print("FAIL: message fabricates the property name as missing")
        sys.exit(1)
    print("OK: property name not blamed")
    sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 2.1 / 2.2 / 2.3: a plainly non-existent attribute still raises
AttributeError, referencing the requested name. HOLDS on both trees
(regression criterion)."""
import sys
from astropy.coordinates import SkyCoord

c = SkyCoord("00h42m30s", "+41d12m00s", frame="icrs")

# hasattr must work (Req 2.3)
if hasattr(c, "definitely_not_a_real_attr_xyz"):
    print("FAIL: hasattr True for absent attr")
    sys.exit(1)

try:
    c.definitely_not_a_real_attr_xyz
    print("FAIL: no exception for absent attr")
    sys.exit(1)
except AttributeError as e:
    msg = str(e)
    print("message:", repr(msg))
    if "definitely_not_a_real_attr_xyz" in msg:
        print("OK: AttributeError references requested name")
        sys.exit(0)
    print("FAIL: message does not reference the requested absent name")
    sys.exit(1)
except Exception as e:
    print("FAIL: wrong exception type:", type(e).__name__)
    sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.3: public name available on the embedded frame is delegated.
Also Req 3.4: transform-target interpretation still works. Regression,
HOLDS on both trees."""
import sys
import numpy as np
from astropy.coordinates import SkyCoord

c = SkyCoord("00h42m30s", "+41d12m00s", frame="icrs")

ok = True
# 3.3 embedded-frame delegation: 'ra'/'dec' come from the icrs frame
try:
    ra = c.ra
    dec = c.dec
    print("ra:", ra, "dec:", dec)
except Exception as e:
    print("FAIL delegation ra/dec:", type(e).__name__, e)
    ok = False

# 3.4 transform-target interpretation: 'galactic' is a frame to transform to
try:
    g = c.galactic
    print("galactic:", g.frame.name if hasattr(g, "frame") else g)
    if g.frame.name != "galactic":
        print("FAIL: transform target did not yield galactic frame")
        ok = False
except Exception as e:
    print("FAIL transform galactic:", type(e).__name__, e)
    ok = False

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 3.1 (frame-name alias returns self) and Req 3.5 (immutability of
alias / transformable-frame names on __setattr__). Regression, HOLDS both."""
import sys
from astropy.coordinates import SkyCoord

c = SkyCoord("00h42m30s", "+41d12m00s", frame="icrs")
ok = True

# 3.1 requesting the current frame's own name alias returns the instance itself
try:
    res = c.icrs
    if res is not c:
        print("FAIL: c.icrs did not return the SkyCoord instance itself; got", type(res))
        ok = False
    else:
        print("OK: c.icrs returned self")
except Exception as e:
    print("FAIL alias icrs:", type(e).__name__, e)
    ok = False

# 3.5 immutability: cannot set a frame-alias / transformable-frame name
for name in ("icrs", "galactic"):
    try:
        setattr(c, name, 123)
        print(f"FAIL: setting '{name}' was allowed (should be immutable)")
        ok = False
    except AttributeError as e:
        print(f"OK: setting '{name}' raised AttributeError: {e}")
    except Exception as e:
        print(f"FAIL: setting '{name}' raised {type(e).__name__} not AttributeError")
        ok = False

sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 3.2: a frame attribute registered in the transform graph is returned
with the correct value. 'obstime'/'equinox'-style extra frame attributes.
Use a distinctive frame attribute value carried on the SkyCoord.
Regression, HOLDS both trees."""
import sys
from astropy.coordinates import SkyCoord
from astropy.time import Time

# FK4 has an 'obstime' frame attribute registered in the transform graph.
t = Time("J2000")
c = SkyCoord("00h42m30s", "+41d12m00s", frame="fk4", obstime=t)

try:
    val = c.obstime
    print("obstime:", val)
    if val is None:
        print("FAIL: obstime resolved to None")
        sys.exit(1)
    # value should be the time we passed
    if abs((val - t).sec) > 1e-6:
        print("FAIL: obstime value differs from what was set")
        sys.exit(1)
    print("OK: frame attribute obstime returned correct value")
    sys.exit(0)
except Exception as e:
    print("FAIL:", type(e).__name__, e)
    sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control — Req 1.3 / 1.2 / 1.4.
A subclass property whose body accesses a missing attribute must raise an
AttributeError that names the *inner* missing attribute ('random_attr'),
NOT the property's own name ('prop').

HOLDS on patched tree; FAILS at base (base fabricates a 'prop' message)."""
import sys
from astropy.coordinates import SkyCoord


class custom_coord(SkyCoord):
    @property
    def prop(self):
        return self.random_attr


c = custom_coord("00h42m30s", "+41d12m00s", frame="icrs")
try:
    c.prop
    print("NO EXCEPTION RAISED — criterion violated")
    sys.exit(1)
except AttributeError as e:
    msg = str(e)
    print("AttributeError message:", repr(msg))
    if "random_attr" in msg:
        print("OK: reports the genuinely missing inner attribute")
        sys.exit(0)
    print("FAIL: message does not mention 'random_attr' (blames the property)")
    sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance astropy-14096: __getattr__ non-resolving path must defer to __getattribute__ so the AttributeError names the genuinely-missing inner attribute rather than the fabricated requested/property name.

Probes (all standalone python, repo pkg only):
- probe_1 (POSITIVE CONTROL, Req 1.2/1.3/1.4): subclass property `prop` accessing missing `self.random_attr`; message must contain 'random_attr'. HOLDS patched ("...has no attribute 'random_attr'"), FAILS at base ("...'prop'"). Discriminates.
- probe_2 (Req 1.4 negative): same scenario; message must NOT report 'prop' as missing. HOLDS patched, FAILS at base.
- probe_3 (Req 2.1/2.2/2.3): genuinely absent attr -> AttributeError referencing requested name; hasattr()==False. HOLDS both (regression).
- probe_4 (Req 3.3/3.4): embedded-frame delegation (ra/dec) and transform-target ('galactic'). HOLDS both.
- probe_5 (Req 3.1/3.5): current-frame alias 'icrs' returns self; setattr on alias/transformable names raises AttributeError (immutable). HOLDS both.
- probe_6 (Req 3.2): registered frame attribute 'obstime' on fk4 returns correct value. HOLDS both.

All 6 hold on gold-patched tree. Positive control fails at base -> prepatch reproduced.

CANDIDATE (weak.diff): the lazy fix that defers to __getattribute__ but re-wraps the AttributeError with the originally-requested name (still blames the property). Applies cleanly at base_commit. Under this patch the suite REJECTS it: probe_1 exit=1 and probe_2 exit=1 (message = "...'prop'"), while regression probes 3,4,5,6 all pass (exit=0). This demonstrates the probe suite discriminates a requirements-plausible-but-wrong implementation; it also would not resolve the hidden test test_subclass_property_exception_error (pytest.raises match='random_attr').

Verdict SOUND: >=5 probes hold on patched, positive control discriminates (holds patched / fails base), and a wrong-fix candidate is rejected by the suite.

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
"""Positive control — Req 1.3 / 1.2 / 1.4.
A subclass property whose body accesses a missing attribute must raise an
AttributeError that names the *inner* missing attribute ('random_attr'),
NOT the property's own name ('prop').

HOLDS on patched tree; FAILS at base (base fabricates a 'prop' message)."""
import sys
from astropy.coordinates import SkyCoord


class custom_coord(SkyCoord):
    @property
    def prop(self):
        return self.random_attr


c = custom_coord("00h42m30s", "+41d12m00s", frame="icrs")
try:
    c.prop
    print("NO EXCEPTION RAISED — criterion violated")
    sys.exit(1)
except AttributeError as e:
    msg = str(e)
    print("AttributeError message:", repr(msg))
    if "random_attr" in msg:
        print("OK: reports the genuinely missing inner attribute")
        sys.exit(0)
    print("FAIL: message does not mention 'random_attr' (blames the property)")
    sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance astropy-14096: __getattr__ non-resolving path must defer to __getattribute__ so the AttributeError names the genuinely-missing inner attribute rather than the fabricated requested/property name.

Probes (all standalone python, repo pkg only):
- probe_1 (POSITIVE CONTROL, Req 1.2/1.3/1.4): subclass property `prop` accessing missing `self.random_attr`; message must contain 'random_attr'. HOLDS patched ("...has no attribute 'random_attr'"), FAILS at base ("...'prop'"). Discriminates.
- probe_2 (Req 1.4 negative): same scenario; message must NOT report 'prop' as missing. HOLDS patched, FAILS at base.
- probe_3 (Req 2.1/2.2/2.3): genuinely absent attr -> AttributeError referencing requested name; hasattr()==False. HOLDS both (regression).
- probe_4 (Req 3.3/3.4): embedded-frame delegation (ra/dec) and transform-target ('galactic'). HOLDS both.
- probe_5 (Req 3.1/3.5): current-frame alias 'icrs' returns self; setattr on alias/transformable names raises AttributeError (immutable). HOLDS both.
- probe_6 (Req 3.2): registered frame attribute 'obstime' on fk4 returns correct value. HOLDS both.

All 6 hold on gold-patched tree. Positive control fails at base -> prepatch reproduced.

CANDIDATE (weak.diff): the lazy fix that defers to __getattribute__ but re-wraps the AttributeError with the originally-requested name (still blames the property). Applies cleanly at base_commit. Under this patch the suite REJECTS it: probe_1 exit=1 and probe_2 exit=1 (message = "...'prop'"), while regression probes 3,4,5,6 all pass (exit=0). This demonstrates the probe suite discriminates a requirements-plausible-but-wrong implementation; it also would not resolve the hidden test test_subclass_property_exception_error (pytest.raises match='random_attr').

Verdict SOUND: >=5 probes hold on patched, positive control discriminates (holds patched / fails base), and a wrong-fix candidate is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed gold-patched tree: (Req1-4) custom_coord property `prop` accessing missing `random_attr` now raises AttributeError naming 'random_attr' (patched) vs 'prop' (base — VIOLATED, confirming previous misleading behavior). (Req2) genuinely-absent name `nonexistent_xyz` still raises AttributeError naming that requested name. (Req3) frame delegation `c.ra` and transform target `c.icrs` still work. Requirements correctly pin the changed observable behavior (deferring to ordinary attribute protocol so the reported name is the genuinely-missing one) rather than a narrow slice or an invented behavior. No forbidden/mandated behavior mismatch found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior abstractly and stay well within what the public problem_statement already discloses. The problem_statement itself gives the full reproducer (subclass custom_coord, property `prop`, missing inner attribute `random_attr`, and the misleading 'object has no attribute prop' message). Notably, requirements.md does NOT even reuse those concrete identifiers — it speaks generically of 'a descriptor (such as a property) whose body accesses a further attribute that does not exist,' so it discloses LESS than the public text. The gold edit replaces the hand-built AttributeError with `return self.__getattribute__(attr)`; the doc paraphrases this as 'defer to the object's ordinary attribute-access protocol for the same name' — a behavioral description, not a quotation of the fix identifier. The FAIL_TO_PASS test name (test_subclass_property_exception_error) and file path are never mentioned. Requirement 3's enumeration of the four resolution branches (frame-name alias, frame-attribute, embedded-frame delegation, transform-target) is derived from the module source being localized, not from the hidden PASS_TO_PASS parametrizations (round_tripping/skycoord_three_components etc.), which are large and NOT mirrored anywhere in the prose. No test code, no gold-patch lines, no fix-invented identifiers, no case enumerations tracking the test parametrization. Legitimate localization + behavioral translation only.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
