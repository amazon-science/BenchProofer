# P2 adversarial audit — sympy__sympy-24661

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
import sys
from sympy.parsing.sympy_parser import parse_expr
from sympy import Lt, Integer
from sympy.core.relational import Relational

r = parse_expr('1 < 2', evaluate=False)
print("result:", repr(r), "type:", type(r))
expected = Lt(Integer(1), Integer(2), evaluate=False)
ok = isinstance(r, Relational) and r == expected and not isinstance(r, bool)
print("expected:", repr(expected), "ok:", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from sympy.parsing.sympy_parser import parse_expr
from sympy import Lt, Le, Gt, Ge, Eq, Ne, Integer

cases = [
    ('1 < 2',  Lt(Integer(1), Integer(2), evaluate=False)),
    ('1 <= 2', Le(Integer(1), Integer(2), evaluate=False)),
    ('1 > 2',  Gt(Integer(1), Integer(2), evaluate=False)),
    ('1 >= 2', Ge(Integer(1), Integer(2), evaluate=False)),
    ('1 == 2', Eq(Integer(1), Integer(2), evaluate=False)),
    ('1 != 2', Ne(Integer(1), Integer(2), evaluate=False)),
]
allok = True
for s, exp in cases:
    r = parse_expr(s, evaluate=False)
    ok = (type(r) == type(exp)) and (r == exp)
    print(f"{s!r} -> {r!r} (expected {exp!r}) ok={ok}")
    allok = allok and ok
sys.exit(0 if allok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from sympy.parsing.sympy_parser import parse_expr
from sympy import Symbol
from sympy.core.relational import Relational

# operand order preserved: 'a < b' should have lhs=a, rhs=b (Req2.2)
r = parse_expr('a < b', evaluate=False)
print("result:", repr(r))
a, b = Symbol('a'), Symbol('b')
ok = isinstance(r, Relational) and r.lhs == a and r.rhs == b
print("lhs:", r.lhs, "rhs:", r.rhs, "ok:", ok)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
from sympy.parsing.sympy_parser import parse_expr
from sympy import Add, Integer
from sympy.core.relational import Relational

# nested arithmetic within operands held unevaluated (Req2.3)
r = parse_expr('1 + 1 < 2 + 2', evaluate=False)
print("result:", repr(r))
ok = isinstance(r, Relational)
# operands should be unevaluated Add, not collapsed to 2 and 4
lhs, rhs = r.lhs, r.rhs
print("lhs:", repr(lhs), "rhs:", repr(rhs))
ok = ok and isinstance(lhs, Add) and isinstance(rhs, Add)
ok = ok and lhs == Add(Integer(1), Integer(1), evaluate=False)
ok = ok and rhs == Add(Integer(2), Integer(2), evaluate=False)
print("ok:", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from sympy.parsing.sympy_parser import parse_expr
from sympy.core.relational import Relational
from sympy import S

# Req1.7: not collapsed to bool even for decidable concrete numbers
allok = True
for s in ['1 < 2', '2 < 1', '3 == 3', '5 != 5']:
    r = parse_expr(s, evaluate=False)
    is_bool = isinstance(r, bool) or r is S.true or r is S.false
    ok = isinstance(r, Relational) and not is_bool
    print(f"{s!r} -> {r!r} type={type(r)} ok={ok}")
    allok = allok and ok
sys.exit(0 if allok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
from sympy.parsing.sympy_parser import parse_expr
from sympy import Add, Mul, Pow, Integer, Symbol

# Req3.1: arithmetic under evaluate=False still held unevaluated
x = Symbol('x')
r1 = parse_expr('1 + 1', evaluate=False)
r2 = parse_expr('2*3', evaluate=False)
r3 = parse_expr('x**2', evaluate=False)
print("r1:", repr(r1), "r2:", repr(r2), "r3:", repr(r3))
ok = (isinstance(r1, Add) and r1 == Add(Integer(1), Integer(1), evaluate=False))
ok = ok and (isinstance(r2, Mul) and r2 == Mul(Integer(2), Integer(3), evaluate=False))
ok = ok and (isinstance(r3, Pow) and r3 == Pow(x, Integer(2), evaluate=False))
print("ok:", ok)
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import sys
from sympy.parsing.sympy_parser import parse_expr
from sympy import S

# Req3.2: default evaluate=True on a comparison of concrete numbers still evaluates
r_true = parse_expr('1 < 2')   # evaluate=True default
r_false = parse_expr('2 < 1')
print("1<2 ->", repr(r_true), "; 2<1 ->", repr(r_false))
ok = (r_true == S.true or r_true is True) and (r_false == S.false or r_false is False)
# also non-comparison unchanged (Req3.3)
r_arith = parse_expr('1 + 1')
print("1+1 ->", repr(r_arith))
ok = ok and (r_arith == 2)
print("ok:", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from sympy.parsing.sympy_parser import parse_expr
from sympy import Lt, Integer
from sympy.core.relational import Relational

r = parse_expr('1 < 2', evaluate=False)
print("result:", repr(r), "type:", type(r))
expected = Lt(Integer(1), Integer(2), evaluate=False)
ok = isinstance(r, Relational) and r == expected and not isinstance(r, bool)
print("expected:", repr(expected), "ok:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: EvaluateFalseTransformer must hold relational operators unevaluated under evaluate=False in parse_expr. Coverage:
- probe_1 (Req1.1, positive control): parse_expr('1 < 2', evaluate=False) == Lt(1,2,evaluate=False), a Relational not a bool. HOLDS patched, FAILS at base (base returns BooleanTrue). Discriminates.
- probe_2 (Req1.1-1.6, Req2.1): all six operators <,<=,>,>=,==,!= map to Lt/Le/Gt/Ge/Eq/Ne held unevaluated. HOLDS patched, FAILS base.
- probe_3 (Req2.2): operand order preserved for 'a < b' (lhs=a, rhs=b). HOLDS patched.
- probe_4 (Req2.3): nested arithmetic in operands held unevaluated ('1+1 < 2+2' -> lhs/rhs are unevaluated Add). HOLDS patched.
- probe_5 (Req1.7): decidable concrete comparisons NOT collapsed to bool. HOLDS patched, FAILS base.
- probe_6 (Req3.1): arithmetic (Add/Mul/Pow) still held unevaluated under evaluate=False. HOLDS both (regression check).
- probe_7 (Req3.2/3.3): default evaluate=True still evaluates comparisons to truth values and 1+1->2. HOLDS both (regression check).

All 7 HOLD on gold-patched tree. Positive control (probe_1) HOLDS patched and FAILS at base (returns BooleanTrue), confirming discriminating power.

Candidate wrong-fix 'partial_lt_only' (weak.diff): a visit_Compare that only rewrites ast.Lt, leaving <=,>,>=,==,!= evaluated. Applies cleanly at base. REJECTED by probe_2 (five operators still evaluate to bool) and probe_5 (== and != still collapse to bool). This demonstrates the suite discriminates a plausibly-wrong partial reading of the requirements. Verdict SOUND: >=5 distinct probes all hold on patched, positive control discriminates base vs patched, and a requirements-under-conforming candidate is rejected.

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
import sys
from sympy.parsing.sympy_parser import parse_expr
from sympy import Lt, Integer
from sympy.core.relational import Relational

r = parse_expr('1 < 2', evaluate=False)
print("result:", repr(r), "type:", type(r))
expected = Lt(Integer(1), Integer(2), evaluate=False)
ok = isinstance(r, Relational) and r == expected and not isinstance(r, bool)
print("expected:", repr(expected), "ok:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: EvaluateFalseTransformer must hold relational operators unevaluated under evaluate=False in parse_expr. Coverage:
- probe_1 (Req1.1, positive control): parse_expr('1 < 2', evaluate=False) == Lt(1,2,evaluate=False), a Relational not a bool. HOLDS patched, FAILS at base (base returns BooleanTrue). Discriminates.
- probe_2 (Req1.1-1.6, Req2.1): all six operators <,<=,>,>=,==,!= map to Lt/Le/Gt/Ge/Eq/Ne held unevaluated. HOLDS patched, FAILS base.
- probe_3 (Req2.2): operand order preserved for 'a < b' (lhs=a, rhs=b). HOLDS patched.
- probe_4 (Req2.3): nested arithmetic in operands held unevaluated ('1+1 < 2+2' -> lhs/rhs are unevaluated Add). HOLDS patched.
- probe_5 (Req1.7): decidable concrete comparisons NOT collapsed to bool. HOLDS patched, FAILS base.
- probe_6 (Req3.1): arithmetic (Add/Mul/Pow) still held unevaluated under evaluate=False. HOLDS both (regression check).
- probe_7 (Req3.2/3.3): default evaluate=True still evaluates comparisons to truth values and 1+1->2. HOLDS both (regression check).

All 7 HOLD on gold-patched tree. Positive control (probe_1) HOLDS patched and FAILS at base (returns BooleanTrue), confirming discriminating power.

Candidate wrong-fix 'partial_lt_only' (weak.diff): a visit_Compare that only rewrites ast.Lt, leaving <=,>,>=,==,!= evaluated. Applies cleanly at base. REJECTED by probe_2 (five operators still evaluate to bool) and probe_5 (== and != still collapse to bool). This demonstrates the suite discriminates a plausibly-wrong partial reading of the requirements. Verdict SOUND: >=5 distinct probes all hold on patched, positive control discriminates base vs patched, and a requirements-under-conforming candidate is rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch adds relational_operators map and visit_Compare to EvaluateFalseTransformer for the six comparison operators Ne/Lt/LtE/Gt/GtE/Eq. Requirements model the observable parse_expr output boundary (not a narrow helper slice) and cover every operator, order, nesting, and the preserved evaluate=True/non-relational paths. Boundary is correct and biconditional against base.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md describes the fix behaviorally: it enumerates the six comparison operators (<,<=,>,>=,==,!=) and maps them to public SymPy relational classes (Lt/Le/Gt/Ge/Eq/Ne) held with evaluate=False. This mirrors the gold patch's relational_operators mapping and the six test cases, BUT: (1) these are public SymPy class names, not fix-invented identifiers; (2) the genuinely fix-invented identifiers (relational_operators dict, visit_Compare method) are NOT disclosed; (3) requirements use abstract 'left'/'right' operands, deliberately avoiding the test's concrete literals '1'/'2'; (4) no test function name (test_issue_24288), file path (test_sympy_parser.py), or verbatim test/gold code appears. The complete operator enumeration is a behavioral description of comparison handling (natural full set), not a reconstruction of the test parametrization. Naming sympy_parser.py / EvaluateFalseTransformer / parse_expr is legitimate localization. The public problem_statement already establishes the < → Lt(1,2,evaluate=False) example and references related issues implying broader operator scope.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
