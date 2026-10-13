# P2 adversarial audit — sympy__sympy-22714

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
# Req 1.1 (positive control): real numeric coords accepted with evaluation disabled
# via the evaluate() context manager. HOLDS patched, FAILS at base.
from sympy import Point2D, Integer
from sympy.core.parameters import evaluate

try:
    with evaluate(False):
        p = Point2D(Integer(1), Integer(2))
except Exception as e:
    print("RAISED under evaluate(False):", type(e).__name__, e)
    raise SystemExit(1)

print("constructed:", p, "coords:", p.args)
raise SystemExit(0 if p == Point2D(1, 2) else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.2 & 1.3: real coords accepted with explicit evaluate=False; Point3D for 3 coords.
from sympy import Point2D, Point3D, Point, Integer

# explicit evaluate=False, 2D
p2 = Point(Integer(1), Integer(2), evaluate=False)
assert isinstance(p2, Point2D), ("not Point2D", type(p2))
assert p2 == Point2D(1, 2), ("2D coords wrong", p2)

# explicit evaluate=False, 3D
p3 = Point(Integer(1), Integer(2), Integer(3), evaluate=False)
assert isinstance(p3, Point3D), ("not Point3D", type(p3))
assert p3 == Point3D(1, 2, 3), ("3D coords wrong", p3)

print("2D:", p2, "3D:", p3)
raise SystemExit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 2.1: genuinely imaginary numeric coords still rejected, both eval settings.
from sympy import Point, I, Integer
from sympy.core.parameters import evaluate

def rejects(fn):
    try:
        fn()
        return False
    except ValueError as e:
        return "Imaginary coordinates are not permitted" in str(e)
    except Exception:
        return False

# eval on
assert rejects(lambda: Point(Integer(1), 2*I)), "did not reject imaginary (eval on)"
# eval off via context manager
assert rejects(lambda: (evaluate(False).__enter__(), Point(Integer(1), 2*I))), \
    "did not reject imaginary (eval off ctx)"
# explicit evaluate=False
assert rejects(lambda: Point(Integer(1), 2*I, evaluate=False)), \
    "did not reject imaginary (evaluate=False)"

print("all imaginary constructions rejected with correct message")
raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 2.3: symbolic / non-concrete coordinate must NOT be rejected as imaginary.
from sympy import Point, Point2D, Symbol
from sympy.core.parameters import evaluate

x = Symbol('x')  # numeric status not established
p = Point(x, 2)
assert isinstance(p, Point2D), ("symbolic coord rejected/altered", type(p))

with evaluate(False):
    p2 = Point(x, 2)
assert isinstance(p2, Point2D), ("symbolic coord rejected under eval off", type(p2))

print("symbolic coords accepted:", p, p2)
raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 3.1,3.2,3.4: regression protection for other validation errors.
import warnings; warnings.filterwarnings("ignore")
from sympy import Point
from sympy.logic.boolalg import true

def raises(fn, exc, msgpart):
    try:
        fn()
    except exc as e:
        return msgpart in str(e)
    except Exception as e:
        print("wrong exc:", type(e).__name__, e)
        return False
    print("no exception raised")
    return False

# 3.1: fewer than two coords (as a sequence) -> ValueError about 2 or more
assert raises(lambda: Point([1]), ValueError, "2 or more coordinates"), \
    "single-coord not rejected"

# 3.2: coordinate that is not a valid SymPy expression -> TypeError
assert raises(lambda: Point(1, true), TypeError, "valid SymPy expressions"), \
    "invalid expr not TypeError"

# 3.4: reducing dimension while removing nonzero coord -> ValueError
assert raises(lambda: Point(1, 2, 3, dim=2), ValueError, "Nonzero coordinates cannot be removed"), \
    "nonzero-removal not rejected"

print("regression validation errors preserved")
raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 3.5: float coords converted to rational + simplified when eval on;
# left unconverted when eval off. Also Req 1.4 real-accept.
from sympy import Point2D, Float, Rational
from sympy.core.parameters import evaluate

# eval on: floats -> rational
p = Point2D(0.5, 0.25)
assert p.x == Rational(1, 2) and p.y == Rational(1, 4), ("not rationalized", p.args)

# eval off: left unconverted (still a Float)
with evaluate(False):
    q = Point2D(0.5, 0.25, evaluate=False)
assert any(isinstance(c, Float) for c in q.args), ("floats got converted under eval off", q.args)

print("eval-on rational:", p.args, "| eval-off:", q.args)
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.1 (positive control): real numeric coords accepted with evaluation disabled
# via the evaluate() context manager. HOLDS patched, FAILS at base.
from sympy import Point2D, Integer
from sympy.core.parameters import evaluate

try:
    with evaluate(False):
        p = Point2D(Integer(1), Integer(2))
except Exception as e:
    print("RAISED under evaluate(False):", type(e).__name__, e)
    raise SystemExit(1)

print("constructed:", p, "coords:", p.args)
raise SystemExit(0 if p == Point2D(1, 2) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fix: change imaginary-coord guard from `a.is_number and im(a)` to `a.is_number and im(a).is_zero is False`, so real numeric coords are accepted when evaluation is disabled (im(1) doesn't simplify to 0 under eval-off; the truthy test misfired at base).

Probes (all HOLD on gold-patched tree; runner re-checks):
- probe_1 (Req 1.1, POSITIVE CONTROL): Point2D(Integer(1),Integer(2)) under evaluate(False) constructs without raising and equals Point2D(1,2). HOLDS patched, VIOLATED at base (raises 'Imaginary coordinates are not permitted.') => discriminates.
- probe_2 (Req 1.2/1.3): explicit evaluate=False -> Point2D for 2 coords, Point3D for 3, correct coord values.
- probe_3 (Req 2.1): genuinely imaginary coord 2*I rejected with correct ValueError message under eval-on, eval-off ctx, and evaluate=False.
- probe_4 (Req 2.3): symbolic coord (Symbol x, numeric status unestablished) accepted, not rejected as imaginary, both eval settings.
- probe_5 (Req 3.1/3.2/3.4): regression — Point([1]) -> ValueError '2 or more coordinates'; Point(1,true) -> TypeError 'valid SymPy expressions'; Point(1,2,3,dim=2) -> ValueError 'Nonzero coordinates cannot be removed'.
- probe_6 (Req 3.5): eval-on floats rationalized (0.5->1/2); eval-off floats left as Float.

Candidate wrong patch weakA (replaces guard predicate with constant False, i.e. removes the imaginary check entirely): a lazy over-broad reading of Req 1. Probes 1,2,4,5,6 HOLD under it but probe_3 REJECTS it (imaginary 2*I no longer raises) => suite discriminates the wrong fix; not a too-weak finding. Verdict SOUND: >=5 distinct probes all hold on patched, positive control discriminates base->patched, and a plausibly-wrong alternative is rejected by the suite.

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
# Req 1.1 (positive control): real numeric coords accepted with evaluation disabled
# via the evaluate() context manager. HOLDS patched, FAILS at base.
from sympy import Point2D, Integer
from sympy.core.parameters import evaluate

try:
    with evaluate(False):
        p = Point2D(Integer(1), Integer(2))
except Exception as e:
    print("RAISED under evaluate(False):", type(e).__name__, e)
    raise SystemExit(1)

print("constructed:", p, "coords:", p.args)
raise SystemExit(0 if p == Point2D(1, 2) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fix: change imaginary-coord guard from `a.is_number and im(a)` to `a.is_number and im(a).is_zero is False`, so real numeric coords are accepted when evaluation is disabled (im(1) doesn't simplify to 0 under eval-off; the truthy test misfired at base).

Probes (all HOLD on gold-patched tree; runner re-checks):
- probe_1 (Req 1.1, POSITIVE CONTROL): Point2D(Integer(1),Integer(2)) under evaluate(False) constructs without raising and equals Point2D(1,2). HOLDS patched, VIOLATED at base (raises 'Imaginary coordinates are not permitted.') => discriminates.
- probe_2 (Req 1.2/1.3): explicit evaluate=False -> Point2D for 2 coords, Point3D for 3, correct coord values.
- probe_3 (Req 2.1): genuinely imaginary coord 2*I rejected with correct ValueError message under eval-on, eval-off ctx, and evaluate=False.
- probe_4 (Req 2.3): symbolic coord (Symbol x, numeric status unestablished) accepted, not rejected as imaginary, both eval settings.
- probe_5 (Req 3.1/3.2/3.4): regression — Point([1]) -> ValueError '2 or more coordinates'; Point(1,true) -> TypeError 'valid SymPy expressions'; Point(1,2,3,dim=2) -> ValueError 'Nonzero coordinates cannot be removed'.
- probe_6 (Req 3.5): eval-on floats rationalized (0.5->1/2); eval-off floats left as Float.

Candidate wrong patch weakA (replaces guard predicate with constant False, i.e. removes the imaginary check entirely): a lazy over-broad reading of Req 1. Probes 1,2,4,5,6 HOLD under it but probe_3 REJECTS it (imaginary 2*I no longer raises) => suite discriminates the wrong fix; not a too-weak finding. Verdict SOUND: >=5 distinct probes all hold on patched, positive control discriminates base->patched, and a plausibly-wrong alternative is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe on gold-patched tree: HOLDS exit=0 (ctxmgr ok, explicit ok, imaginary rejected in both eval modes, symbolic ok). Same probe --base: VIOLATED exit=1 (raises Imaginary coordinates are not permitted at point.py:156). The requirements pin the changed observable behavior (accept real numeric coords when im part is zero-or-undetermined; reject only definitely-nonzero imaginary), which is exactly the boundary the patch's `.is_zero is False` implements — not a narrow branch/helper slice. Requirement 1.4's 'cannot be determined to be nonzero -> permissible' precisely captures the tri-state fuzzy-bool distinction that fixes the disabled-evaluation case.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** requirements.md contains no hidden-test artifacts: no test file paths, no test function/class names (test_issue_22684 never appears), no parametrization ids, no quoted test/gold code. The one concrete example (Point2D(Integer(1), Integer(2))) is drawn verbatim from the PUBLIC problem_statement, as is the ValueError message and the evaluate(False) crash scenario. Req 1.4/Req 2 ('imaginary part cannot be determined to be nonzero' / 'definitely nonzero') is a legitimate behavioral translation of the gold predicate im(a).is_zero is False, not a quotation — this is the intended purpose of the spec. Identifiers named (Point/Point2D/Point3D.__new__, im, on_morph, sympify/parse_expr) are pre-existing public API used to localize the change, not fix-invented. Req 3's regression list describes general pre-existing construction/validation behavior and does not mirror the PASS_TO_PASS parametrization as an id list.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
