# P2 adversarial audit — sympy__sympy-19346

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
#!/usr/bin/env python
# R1.2/R1.6 (positive control): srepr of a dict of Symbols renders keys/values in srepr form
import sys
from sympy import symbols
from sympy.printing.repr import srepr

x, y = symbols('x y')
out = srepr({x: y})
print("srepr({x: y}) =", repr(out))
expected = "{Symbol('x'): Symbol('y')}"
if out == expected:
    print("HOLDS")
    sys.exit(0)
print("FAIL, expected", repr(expected))
sys.exit(1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# R1.3 & R1.7: multi-entry dict joins with ", " and preserves insertion order
import sys
from sympy import symbols
from sympy.printing.repr import srepr

x, y, z = symbols('x y z')
d = {x: y, z: x}  # insertion order x,z
out = srepr(d)
print("srepr =", repr(out))
expected = "{Symbol('x'): Symbol('y'), Symbol('z'): Symbol('x')}"
if out == expected:
    print("HOLDS")
    sys.exit(0)
print("FAIL, expected", repr(expected))
sys.exit(1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# R1.4 empty dict -> "{}", R1.5 nested dict recursion
import sys
from sympy import symbols
from sympy.printing.repr import srepr

x, y, z = symbols('x y z')
empty = srepr({})
print("srepr({}) =", repr(empty))
nested = srepr({x: {y: z}})
print("srepr({x:{y:z}}) =", repr(nested))
ok = True
if empty != "{}":
    print("FAIL empty"); ok = False
if nested != "{Symbol('x'): {Symbol('y'): Symbol('z')}}":
    print("FAIL nested"); ok = False
if ok:
    print("HOLDS"); sys.exit(0)
sys.exit(1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# R2.1/R2.2/R2.4/R2.5: set of Symbols in srepr form, each once, delimiters
import sys
from sympy import symbols
from sympy.printing.repr import srepr

x, y = symbols('x y')
out = srepr({x, y})
print("srepr({x,y}) =", repr(out))
ok = True
if not (out.startswith("{") and out.endswith("}")):
    print("FAIL delimiters"); ok = False
# should be a set of exactly the two srepr elements joined by ", "
parts = out[1:-1].split(", ")
if sorted(parts) != ["Symbol('x')", "Symbol('y')"]:
    print("FAIL elements", parts); ok = False
if ok:
    print("HOLDS"); sys.exit(0)
sys.exit(1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# R2.3: empty set -> "set()" and NOT "{}"
import sys
from sympy.printing.repr import srepr

out = srepr(set())
print("srepr(set()) =", repr(out))
if out == "set()":
    print("HOLDS"); sys.exit(0)
print("FAIL"); sys.exit(1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# R3 regression: list, tuple, and scalar srepr unchanged
import sys
from sympy import symbols, Integer, Rational
from sympy.printing.repr import srepr

x, y = symbols('x y')
ok = True
lst = srepr([x, y])
print("list:", repr(lst))
if lst != "[Symbol('x'), Symbol('y')]":
    print("FAIL list"); ok = False
tup = srepr((x, y))
print("tuple:", repr(tup))
if tup != "(Symbol('x'), Symbol('y'))":
    print("FAIL tuple"); ok = False
i = srepr(Integer(5))
print("Integer:", repr(i))
if i != "Integer(5)":
    print("FAIL Integer"); ok = False
r = srepr(Rational(1, 2))
print("Rational:", repr(r))
if r != "Rational(1, 2)":
    print("FAIL Rational"); ok = False
if ok:
    print("HOLDS"); sys.exit(0)
sys.exit(1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
#!/usr/bin/env python
# R1.2/R1.6 (positive control): srepr of a dict of Symbols renders keys/values in srepr form
import sys
from sympy import symbols
from sympy.printing.repr import srepr

x, y = symbols('x y')
out = srepr({x: y})
print("srepr({x: y}) =", repr(out))
expected = "{Symbol('x'): Symbol('y')}"
if out == expected:
    print("HOLDS")
    sys.exit(0)
print("FAIL, expected", repr(expected))
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: make srepr render dict/set containers recursively (gold adds _print_dict and _print_set to ReprPrinter). Probes cover: R1.2/R1.6 dict of Symbols (probe_1, positive control), R1.3/R1.7 multi-entry join & insertion order (probe_2), R1.4 empty dict '{}' + R1.5 nested recursion (probe_3), R2.1/R2.2/R2.4/R2.5 set of Symbols order-agnostic (probe_4), R2.3 empty set 'set()' not '{}' (probe_5), R3 regression list/tuple/Integer/Rational unchanged (probe_6).

Results on gold-PATCHED tree: all 6 HOLD (exit 0).
At BASE: probe_1 VIOLATED ('{x: y}'), probe_3 VIOLATED (nested '{x: {y: z}}'), probe_4 VIOLATED ('{x, y}'). probe_5 and probe_6 HOLD at base (base already returns 'set()' for empty set and never changed list/tuple/scalars) — these are pure regression guards. Positive control probe_1 discriminates: FAIL@base, HOLD@patched.

Candidate wrong-fix (dict_only_partial_fix): implements only _print_dict, omitting _print_set. Under it probe_1/2/3/5/6 HOLD but probe_4 is REJECTED (srepr({x,y}) -> '{y, x}', bare names) — the suite discriminates this partial fix. This candidate would also fail the hidden set-related tests. No requirements-conforming candidate found that would fail the harness; the spec pins both dict and set behaviors tightly (empty forms, recursion, srepr element form, delimiters, regression), matching the gold patch exactly.

All needed runs completed successfully in the instance image.

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
#!/usr/bin/env python
# R1.2/R1.6 (positive control): srepr of a dict of Symbols renders keys/values in srepr form
import sys
from sympy import symbols
from sympy.printing.repr import srepr

x, y = symbols('x y')
out = srepr({x: y})
print("srepr({x: y}) =", repr(out))
expected = "{Symbol('x'): Symbol('y')}"
if out == expected:
    print("HOLDS")
    sys.exit(0)
print("FAIL, expected", repr(expected))
sys.exit(1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: make srepr render dict/set containers recursively (gold adds _print_dict and _print_set to ReprPrinter). Probes cover: R1.2/R1.6 dict of Symbols (probe_1, positive control), R1.3/R1.7 multi-entry join & insertion order (probe_2), R1.4 empty dict '{}' + R1.5 nested recursion (probe_3), R2.1/R2.2/R2.4/R2.5 set of Symbols order-agnostic (probe_4), R2.3 empty set 'set()' not '{}' (probe_5), R3 regression list/tuple/Integer/Rational unchanged (probe_6).

Results on gold-PATCHED tree: all 6 HOLD (exit 0).
At BASE: probe_1 VIOLATED ('{x: y}'), probe_3 VIOLATED (nested '{x: {y: z}}'), probe_4 VIOLATED ('{x, y}'). probe_5 and probe_6 HOLD at base (base already returns 'set()' for empty set and never changed list/tuple/scalars) — these are pure regression guards. Positive control probe_1 discriminates: FAIL@base, HOLD@patched.

Candidate wrong-fix (dict_only_partial_fix): implements only _print_dict, omitting _print_set. Under it probe_1/2/3/5/6 HOLD but probe_4 is REJECTED (srepr({x,y}) -> '{y, x}', bare names) — the suite discriminates this partial fix. This candidate would also fail the hidden set-related tests. No requirements-conforming candidate found that would fail the harness; the spec pins both dict and set behaviors tightly (empty forms, recursion, srepr element form, delimiters, regression), matching the gold patch exactly.

All needed runs completed successfully in the instance image.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch adds _print_dict (joins '%s: %s' via doprint on each key/value, wraps in {}) and _print_set (empty->'set()', else reprify wrapped in {}). Requirements pin exactly this changed observable srepr output for dict/set plus regression protection for existing types. Boundary is correct: it models the changed srepr behavior, not a narrower slice or single branch. R1.7 (dict iteration order preserved) and R2.5 (each set element once, any order) correctly reflect .items()/reprify iteration and the test's order-agnostic assertions. Probe passed on gold-patched image (exit 0, ALL OK).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes srepr dict/set support behaviorally. Module/class names (sympy/printing/repr.py, ReprPrinter) are legitimate localization. The gold-invented identifiers (_print_dict, _print_set, reprify, dict_kvs) do NOT appear. No test names (test_dict/test_set), paths (test_repr.py), or quoted test code. Example outputs like Symbol('x')/Symbol('y') follow directly from the PUBLIC problem_statement, which already shows srepr([x,y])==[Symbol('x'), Symbol('y')] and the broken {x,y}/{x:y} cases. The nested example {Symbol('x'): {Symbol('y'): Symbol('z')}} (Req 1.5) coincides with a test case but reads as a natural illustration of the recursion rule using standard abc symbols, not a transcription of the hidden assertion. Empty-dict {} and empty-set set() (Req 1.4/2.3) are Python-language facts / obvious spec points, not test-derived leaks. The set non-determinism is described as behavior (render each element once, any ordering) rather than enumerated as the test's two literal alternative strings.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
