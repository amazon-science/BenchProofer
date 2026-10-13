# P2 adversarial audit — sympy__sympy-23262

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
# Positive control: R1.2/R1.3 - lambdify of one-element tuple returns a length-1 tuple
import sys
from sympy import symbols, lambdify
x = symbols('x')
f = lambdify(x, (1,))
res = f(0)
print("result:", repr(res), "type:", type(res).__name__)
if isinstance(res, tuple) and len(res) == 1 and res == (1,):
    sys.exit(0)
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# R1.1: _recursive_to_string renders single-element tuple with trailing comma,
# and the rendered text evals to a length-1 tuple.
import sys
from sympy.utilities.lambdify import _recursive_to_string
from sympy import Symbol
s = _recursive_to_string(str, (Symbol('a'),))
print("rendered:", repr(s))
val = eval(s, {'a': 1})
print("eval:", repr(val), type(val).__name__)
if isinstance(val, tuple) and len(val) == 1 and ',' in s:
    sys.exit(0)
sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# R2: multi-element tuple renders and evals to a tuple of same length/order.
import sys
from sympy.utilities.lambdify import _recursive_to_string, lambdify
from sympy import symbols
x = symbols('x')
s = _recursive_to_string(str, (symbols('a'), symbols('b'), symbols('c')))
print("rendered:", repr(s))
val = eval(s, {'a': 1, 'b': 2, 'c': 3})
print("eval:", repr(val))
f = lambdify(x, (x, x+1, x+2))
r = f(10)
print("lambdify:", repr(r))
ok = (isinstance(val, tuple) and val == (1, 2, 3)
      and isinstance(r, tuple) and r == (10, 11, 12))
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# R3: list rendering stays a list (not a tuple), preserving order.
import sys
from sympy.utilities.lambdify import _recursive_to_string, lambdify
from sympy import symbols
x = symbols('x')
s = _recursive_to_string(str, [symbols('a'), symbols('b')])
print("rendered:", repr(s))
val = eval(s, {'a': 1, 'b': 2})
print("eval:", repr(val), type(val).__name__)
# single element list must stay a list, NOT gain a trailing comma turning it odd
s1 = _recursive_to_string(str, [symbols('a')])
val1 = eval(s1, {'a': 7})
print("single list rendered:", repr(s1), "->", repr(val1))
f = lambdify(x, [x, x+1])
r = f(5)
print("lambdify list:", repr(r), type(r).__name__)
ok = (isinstance(val, list) and val == [1, 2]
      and isinstance(val1, list) and val1 == [7]
      and isinstance(r, list) and r == [5, 6])
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# R4: nested containers handled elementwise; nested one-element tuple keeps its comma.
import sys
from sympy.utilities.lambdify import _recursive_to_string
from sympy import symbols
a, b = symbols('a b')
# outer list containing a one-element tuple and a 2-tuple
s = _recursive_to_string(str, [(a,), (a, b)])
print("rendered:", repr(s))
val = eval(s, {'a': 4, 'b': 5})
print("eval:", repr(val))
ok = (isinstance(val, list) and len(val) == 2
      and isinstance(val[0], tuple) and val[0] == (4,)
      and isinstance(val[1], tuple) and val[1] == (4, 5))
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# R5.2: single non-container expression is NOT wrapped in a container.
import sys
from sympy import symbols, lambdify
from sympy.utilities.lambdify import _recursive_to_string
x = symbols('x')
f = lambdify(x, x+1)
r = f(3)
print("scalar lambdify:", repr(r), type(r).__name__)
s = _recursive_to_string(str, symbols('a'))
print("scalar render:", repr(s))
ok = (not isinstance(r, (tuple, list)) and r == 4 and s == 'a')
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: R1.2/R1.3 - lambdify of one-element tuple returns a length-1 tuple
import sys
from sympy import symbols, lambdify
x = symbols('x')
f = lambdify(x, (1,))
res = f(0)
print("result:", repr(res), "type:", type(res).__name__)
if isinstance(res, tuple) and len(res) == 1 and res == (1,):
    sys.exit(0)
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree.

Probe->requirement mapping and results (patched exit / base exit):
- probe_1 (R1.2/R1.3, POSITIVE CONTROL): lambdify(x,(1,))(0) returns (1,) tuple. patched HOLDS (result (1,) tuple), base VIOLATED (result 1 int). Discriminates.
- probe_2 (R1.1): _recursive_to_string of one-elem tuple renders '(a,)' with trailing comma, evals to len-1 tuple. patched HOLDS, base VIOLATED (renders '(a)' -> int 1).
- probe_3 (R2.1/R2.2): multi-elem tuple renders '(a, b, c,)' -> (1,2,3); lambdify (x,x+1,x+2)(10)=(10,11,12). HOLDS patched.
- probe_4 (R3.1/R3.2): list renders as list literal, single-elem list [a]->[7] stays list, lambdify list stays list. HOLDS patched.
- probe_5 (R4.1): nested [(a,),(a,b)] -> [(4,),(4,5)] elementwise; nested one-elem tuple keeps comma. HOLDS patched.
- probe_6 (R5.2): scalar expr not wrapped in container; lambdify(x,x+1)(3)=4 int; scalar render 'a'. HOLDS patched.

CANDIDATE PATCH exercised (list_only_fix / weak.diff): fixes only the tuple-unpacking bug ('[]'->'[','], '()'->'(',')') but keeps tuple delimiters '(',')' WITHOUT trailing comma. This is the lazy/partial fix a weak reading permits (it fixes the visible '[]' unpacking typo but not the single-element-tuple semantics). Applies cleanly at base. Probe results under weak.diff: probe_1 VIOLATED, probe_2 VIOLATED, probe_5 VIOLATED (nested one-elem tuple '(a)'->int, list becomes [4,(4,5)]); probes 3,4,6 HOLD. => suite REJECTS the wrong fix on 3 probes. Discriminating power confirmed.

Positive control failed at base and holds patched (prepatch reproduced=true). >=5 probes all hold on patched tree, wrong candidate rejected. Verdict SOUND.

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
# Positive control: R1.2/R1.3 - lambdify of one-element tuple returns a length-1 tuple
import sys
from sympy import symbols, lambdify
x = symbols('x')
f = lambdify(x, (1,))
res = f(0)
print("result:", repr(res), "type:", type(res).__name__)
if isinstance(res, tuple) and len(res) == 1 and res == (1,):
    sys.exit(0)
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree.

Probe->requirement mapping and results (patched exit / base exit):
- probe_1 (R1.2/R1.3, POSITIVE CONTROL): lambdify(x,(1,))(0) returns (1,) tuple. patched HOLDS (result (1,) tuple), base VIOLATED (result 1 int). Discriminates.
- probe_2 (R1.1): _recursive_to_string of one-elem tuple renders '(a,)' with trailing comma, evals to len-1 tuple. patched HOLDS, base VIOLATED (renders '(a)' -> int 1).
- probe_3 (R2.1/R2.2): multi-elem tuple renders '(a, b, c,)' -> (1,2,3); lambdify (x,x+1,x+2)(10)=(10,11,12). HOLDS patched.
- probe_4 (R3.1/R3.2): list renders as list literal, single-elem list [a]->[7] stays list, lambdify list stays list. HOLDS patched.
- probe_5 (R4.1): nested [(a,),(a,b)] -> [(4,),(4,5)] elementwise; nested one-elem tuple keeps comma. HOLDS patched.
- probe_6 (R5.2): scalar expr not wrapped in container; lambdify(x,x+1)(3)=4 int; scalar render 'a'. HOLDS patched.

CANDIDATE PATCH exercised (list_only_fix / weak.diff): fixes only the tuple-unpacking bug ('[]'->'[','], '()'->'(',')') but keeps tuple delimiters '(',')' WITHOUT trailing comma. This is the lazy/partial fix a weak reading permits (it fixes the visible '[]' unpacking typo but not the single-element-tuple semantics). Applies cleanly at base. Probe results under weak.diff: probe_1 VIOLATED, probe_2 VIOLATED, probe_5 VIOLATED (nested one-elem tuple '(a)'->int, list becomes [4,(4,5)]); probes 3,4,6 HOLD. => suite REJECTS the wrong fix on 3 probes. Discriminating power confirmed.

Positive control failed at base and holds patched (prepatch reproduced=true). >=5 probes all hold on patched tree, wrong candidate rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The patch changes exactly two lines in _recursive_to_string: list delimiters ('[','] ') and tuple delimiters ('(',',)'). Requirements pin the changed observable behavior (container round-trip via _recursive_to_string and lambdify), which is the correct modeling boundary — not a narrow slice. R2's rendered '(1, 2,)' carries a harmless extra trailing comma but still evaluates to a tuple of the same length and order, satisfying R2's criteria. Base probe fails at R1's one-element-tuple assertion, confirming the requirements capture the actual regression fix. No forbidden/invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md stays within the public problem_statement. The public MWE already discloses lambdify([], tuple([1])) rendering (1) vs (1,), the missing trailing comma, the integer-element case, and correct multi-element tuple rendering ((1, 2)). The document translates these into behavioral EARS criteria and legitimately localizes the fix to _recursive_to_string in sympy/utilities/lambdify.py (naming the module/function is allowed). No leaks of hidden material: no test function names (test_issue_14941), no test file path, no parametrization ids, no quoted test code (f2b = lambdify([], (1,))), no verbatim gold-patch lines (left/right delimiter assignments '[', ']' / '(', ',)'), and no fix-invented identifiers. Requirements 3-5 (list rendering, nested containers, scalar/no-arg cases) describe general container semantics of the function rather than mirroring the single added test case, and correspond to pre-existing PASS_TO_PASS behavior described only in prose, not enumerated to reconstruct tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
