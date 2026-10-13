# P2 adversarial audit — sympy__sympy-14711

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
from sympy.physics.vector import ReferenceFrame

N = ReferenceFrame('N')
v = 3*N.x + 2*N.y
try:
    r = v + 0
except Exception as e:
    print("FAIL: v+0 raised", repr(e)); sys.exit(1)
print("v+0 =", r)
if r != v:
    print("FAIL: v+0 != v"); sys.exit(1)
print("OK req1.1/1.2: v+0 == v, no exception")
sys.exit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from sympy.physics.vector import ReferenceFrame

N = ReferenceFrame('N')
v = 3*N.x + 2*N.y
try:
    r = 0 + v  # reflected __radd__
except Exception as e:
    print("FAIL: 0+v raised", repr(e)); sys.exit(1)
print("0+v =", r)
if r != v:
    print("FAIL: 0+v != v"); sys.exit(1)
print("OK req1.3: 0+v == v (reflected add)")
sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from sympy.physics.vector import ReferenceFrame

N = ReferenceFrame('N')
vs = [N.x, 2*N.y, 3*N.z]
try:
    s = sum(vs)
except Exception as e:
    print("FAIL: sum raised", repr(e)); sys.exit(1)
expected = N.x + 2*N.y + 3*N.z
print("sum =", s)
if s != expected:
    print("FAIL: sum != expected"); sys.exit(1)
print("OK req1.4: sum([...]) works and equals vector sum")
sys.exit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
from sympy.physics.vector import ReferenceFrame

N = ReferenceFrame('N')
# req2.1 concatenation, req2.2 cancellation, req2.3 preserve dot/neg/scalar/diff
a = 3*N.x + 2*N.y
b = N.x - 2*N.y
if (a + b) != 4*N.x:
    print("FAIL: addition cancellation wrong:", a+b); sys.exit(1)
if (N.x + (-N.x)) != 0*N.x:  # zero vector
    print("FAIL: x + (-x) not zero"); sys.exit(1)
# dot
if (a & b) != 3*1 + 2*(-2):
    print("FAIL: dot product changed:", a & b); sys.exit(1)
# negation
if (-a) != (-3*N.x - 2*N.y):
    print("FAIL: negation changed"); sys.exit(1)
# scalar mult
if (2*a) != (6*N.x + 4*N.y):
    print("FAIL: scalar mult changed"); sys.exit(1)
# difference
if (a - b) != (2*N.x + 4*N.y):
    print("FAIL: difference changed:", a-b); sys.exit(1)
print("OK req2: concatenation/cancellation/dot/neg/scalar/diff preserved")
sys.exit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from sympy.physics.vector import ReferenceFrame

N = ReferenceFrame('N')
v = 3*N.x
# req3.1: non-zero non-vector operand raises TypeError
for bad in [5, 1.0, "x"]:
    try:
        r = v + bad
    except TypeError as e:
        msg = str(e)
        print("got TypeError for", repr(bad), ":", msg)
        # req3.2: message indicates a Vector must be supplied
        if "Vector" not in msg:
            print("FAIL: message does not mention Vector"); sys.exit(1)
    except Exception as e:
        print("FAIL: wrong exception type for", repr(bad), repr(e)); sys.exit(1)
    else:
        print("FAIL: no exception for", repr(bad), "->", r); sys.exit(1)
print("OK req3: non-zero non-vector operands rejected with Vector TypeError")
sys.exit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from sympy.physics.vector import ReferenceFrame

N = ReferenceFrame('N')
v = 3*N.x + 2*N.y
try:
    r = v + 0
except Exception as e:
    print("FAIL: v+0 raised", repr(e)); sys.exit(1)
print("v+0 =", r)
if r != v:
    print("FAIL: v+0 != v"); sys.exit(1)
print("OK req1.1/1.2: v+0 == v, no exception")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy__sympy-14711: gold adds `if other == 0: return self` to Vector.__add__ so scalar 0 becomes the additive identity.

Probes (all re-run in the official image):
- probe_1 (req1.1/1.2, v+0==v, no raise): POSITIVE CONTROL. base=VIOLATED, patched=HOLDS. Discriminates.
- probe_2 (req1.3, reflected 0+v==v): base=VIOLATED, patched=HOLDS.
- probe_3 (req1.4, sum([vectors]) completes & equals vector sum): base=VIOLATED, patched=HOLDS.
- probe_4 (req2.1/2.2/2.3, concat+cancellation+dot/neg/scalar/diff preserved): HOLDS on base and patched (regression guard).
- probe_5 (req3.1/3.2, non-zero non-vector operand -> TypeError mentioning 'Vector'): HOLDS on base and patched.

Candidate wrong-fix `return_empty_vector` (return Vector([]) instead of self): REJECTED by probes 1/2/3 (empty vector != v, and sum comes out empty), HOLDS on probes 4/5. Demonstrates the suite discriminates a plausibly-wrong reading that satisfies 'no exception' but violates 'returns the vector unchanged' (req1.5). No probe-conforming alternative patch found that would fail the hidden tests.

Verdict: SOUND. >=5 distinct probes all hold on the patched tree; positive control fails at base and holds patched; a wrong candidate is rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from sympy.physics.vector import ReferenceFrame

N = ReferenceFrame('N')
v = 3*N.x + 2*N.y
try:
    r = v + 0
except Exception as e:
    print("FAIL: v+0 raised", repr(e)); sys.exit(1)
print("v+0 =", r)
if r != v:
    print("FAIL: v+0 != v"); sys.exit(1)
print("OK req1.1/1.2: v+0 == v, no exception")
sys.exit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy__sympy-14711: gold adds `if other == 0: return self` to Vector.__add__ so scalar 0 becomes the additive identity.

Probes (all re-run in the official image):
- probe_1 (req1.1/1.2, v+0==v, no raise): POSITIVE CONTROL. base=VIOLATED, patched=HOLDS. Discriminates.
- probe_2 (req1.3, reflected 0+v==v): base=VIOLATED, patched=HOLDS.
- probe_3 (req1.4, sum([vectors]) completes & equals vector sum): base=VIOLATED, patched=HOLDS.
- probe_4 (req2.1/2.2/2.3, concat+cancellation+dot/neg/scalar/diff preserved): HOLDS on base and patched (regression guard).
- probe_5 (req3.1/3.2, non-zero non-vector operand -> TypeError mentioning 'Vector'): HOLDS on base and patched.

Candidate wrong-fix `return_empty_vector` (return Vector([]) instead of self): REJECTED by probes 1/2/3 (empty vector != v, and sum comes out empty), HOLDS on probes 4/5. Demonstrates the suite discriminates a plausibly-wrong reading that satisfies 'no exception' but violates 'returns the vector unchanged' (req1.5). No probe-conforming alternative patch found that would fail the hidden tests.

Verdict: SOUND. >=5 distinct probes all hold on the patched tree; positive control fails at base and holds patched; a wrong candidate is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe on gold-patched tree: zerovec(0*N.x)==0 is True, v+(0*N.x)==v True, v+0 is v True, and error message exactly 'A Vector must be supplied'. Requirements pin the changed observable behavior (the ==0 shortcut in both operand orders plus preserved concat and rejection), not a narrow slice. Boundary is correct.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** All content is derivable from the PUBLIC problem_statement: it already shows the sum([N.x, 0*N.x]) idiom, the v+0 addition, the vector.py __add__/_check_vector location, and the verbatim TypeError 'A Vector must be supplied'. Requirements name the module/function (legitimate localization) and translate behavior into EARS criteria. The hidden test name (test_Vector) and its assertion (A.x + 0 == A.x), plus PASS_TO_PASS names (test_Vector_diffs, test_vector_var_in_dcm) and the gold line (`if other == 0: return self`) are NOT quoted or reconstructed. Req 1's 0+v/v+0/sum cases mirror the public example, not a hidden parametrization. No fix-invented identifiers. No test-shaped enumeration.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
