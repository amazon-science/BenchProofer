# P2 adversarial audit — sympy__sympy-20801

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

Counterexample / evidence:

```
weak_A (naive fix: remove the early `if not self: return not other` shortcut but do NOT restore it after the numeric-kind dispatch) is REJECTED by probe_4: it makes Float(0)==S.EmptySet and Float(0)==() return False, violating Requirement 3 (empty/zero-like fallback must survive for non-numeric non-boolean operands). Base tree fails probes 1/2/3: S(0.0)==S.false -> True (asymmetric bug).
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
from sympy import S
# Req1.1 (positive control): zero Float == S.false -> False
r1 = (S(0.0) == S.false)
# Req1.2: zero Float == S.true -> False
r2 = (S(0.0) == S.true)
print("S(0.0)==S.false ->", r1)
print("S(0.0)==S.true  ->", r2)
ok = (r1 is False) and (r2 is False)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from sympy import S
# Req2: order independence for float-vs-boolean and int-vs-boolean
a = (S(0.0) == S.false)
b = (S.false == S(0.0))
c = (S(0) == S.false)
d = (S.false == S(0))
print("S(0.0)==S.false", a, "| S.false==S(0.0)", b)
print("S(0)==S.false", c, "| S.false==S(0)", d)
ok = (a is False) and (b is False) and (a == b) and (c is False) and (d is False) and (c == d)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from sympy import S, Float
# Req1.4: __ne__ with boolean -> True ; and Req1.3 nonzero float vs bool -> False
ne = Float(0).__ne__(S.false)
nz = (Float(2.5) == S.false)
print("Float(0).__ne__(S.false) ->", ne)
print("Float(2.5)==S.false ->", nz)
ok = (ne is True) and (nz is False)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
from sympy import S, Float
# Req3: empty/zero-like fallback preserved for non-numeric non-boolean operands
# EmptySet is zero-like/empty -> zero Float should still equal it True
r_empty = (Float(0) == S.EmptySet)
r_tuple = (Float(0) == ())
# Req4.6: non-numeric non-boolean not-empty operand -> False
r_ne = (Float(0) == "abc")
print("Float(0)==S.EmptySet ->", r_empty)
print("Float(0)==() ->", r_tuple)
print("Float(0)=='abc' ->", r_ne)
ok = (r_empty is True) and (r_tuple is True) and (r_ne is False)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from sympy import S, Float, Rational, Integer, pi
# Req4: numeric regression semantics
checks = {
    "Float==Float same": (Float(1.5) == Float(1.5)) is True,
    "Float diff prec": (Float(.1, 3) == Float(.1, 33)) is False,
    "Float==Integer": (Float(2.0) == Integer(2)) is True,
    "Float==Rational": (Float(0.5) == Rational(1, 2)) is True,
    "Float!=Rational": (Float(0.4) == Rational(1, 2)) is False,
    "Float==pi (irrational NumberSymbol)": (Float(0) == pi) is False,
    "zeroFloat != Integer 1": (Float(0) == Integer(1)) is False,
    "zeroFloat == Integer 0": (Float(0) == Integer(0)) is True,
}
for k, v in checks.items():
    print(k, "->", v)
sys.exit(0 if all(checks.values()) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from sympy import S
# Req1.1 (positive control): zero Float == S.false -> False
r1 = (S(0.0) == S.false)
# Req1.2: zero Float == S.true -> False
r2 = (S(0.0) == S.true)
print("S(0.0)==S.false ->", r1)
print("S(0.0)==S.true  ->", r2)
ok = (r1 is False) and (r2 is False)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold moves the `if not self: return not other` shortcut from before the operand-kind dispatch to after it. 5 distinct probes all HOLD on the gold-patched tree and discriminate. probe_1 (positive control): Req1.1/1.2 zero Float vs S.false/S.true -> False; HOLDS patched, FAILS base (base gives S(0.0)==S.false=True). probe_2: Req2 order-independence for float-vs-bool and int-vs-bool (all False both orderings); FAILS base. probe_3: Req1.3/1.4 __ne__ with bool -> True and nonzero float vs bool -> False; FAILS base. probe_4: Req3/Req4.6 empty/zero-like fallback preserved (Float(0)==EmptySet/() -> True) and non-empty non-numeric -> False; this probe REJECTS candidate weak_A, proving the suite discriminates a requirements-plausible-but-wrong partial fix. probe_5: Req4 numeric regression semantics (Float==Float exact/precision, Integer, Rational, irrational NumberSymbol pi, zero vs nonzero) all HOLD patched. Candidate weak_A exercised and rejected. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
weak_A (naive fix: remove the early `if not self: return not other` shortcut but do NOT restore it after the numeric-kind dispatch) is REJECTED by probe_4: it makes Float(0)==S.EmptySet and Float(0)==() return False, violating Requirement 3 (empty/zero-like fallback must survive for non-numeric non-boolean operands). Base tree fails probes 1/2/3: S(0.0)==S.false -> True (asymmetric bug).
```

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
from sympy import S
# Req1.1 (positive control): zero Float == S.false -> False
r1 = (S(0.0) == S.false)
# Req1.2: zero Float == S.true -> False
r2 = (S(0.0) == S.true)
print("S(0.0)==S.false ->", r1)
print("S(0.0)==S.true  ->", r2)
ok = (r1 is False) and (r2 is False)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Gold moves the `if not self: return not other` shortcut from before the operand-kind dispatch to after it. 5 distinct probes all HOLD on the gold-patched tree and discriminate. probe_1 (positive control): Req1.1/1.2 zero Float vs S.false/S.true -> False; HOLDS patched, FAILS base (base gives S(0.0)==S.false=True). probe_2: Req2 order-independence for float-vs-bool and int-vs-bool (all False both orderings); FAILS base. probe_3: Req1.3/1.4 __ne__ with bool -> True and nonzero float vs bool -> False; FAILS base. probe_4: Req3/Req4.6 empty/zero-like fallback preserved (Float(0)==EmptySet/() -> True) and non-empty non-numeric -> False; this probe REJECTS candidate weak_A, proving the suite discriminates a requirements-plausible-but-wrong partial fix. probe_5: Req4 numeric regression semantics (Float==Float exact/precision, Integer, Rational, irrational NumberSymbol pi, zero vs nonzero) all HOLD patched. Candidate weak_A exercised and rejected. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The patch relocates `if not self: return not other` from before the kind-dispatch to after the Boolean and numeric-kind checks in Float.__eq__. Requirement 3 correctly captures this as the true modeling boundary: the zero-float shortcut is retained but demoted below Boolean/numeric handling, rather than deleted. Requirements do not overclaim (no invented behavior) nor underclaim (they pin the full changed behavior incl. order independence and regression protection). FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe behavior derivable from the PUBLIC problem_statement, which already contains all four verbatim comparisons: S(0.0)==S.false (True/wrong), S.false==S(0.0) (False), S(0)==S.false (False), S.false==S(0) (False). Reqs 1.1, 2.1, 2.2 restate exactly these public examples. Naming Float.__eq__/__ne__, Boolean, and sympy/core/numbers.py is legitimate localization of the change. Req 3's account of the empty/zero-like shortcut being moved to run only for non-boolean/non-numeric operands is a behavioral translation of the fix, not quoted gold code (the gold patch simply relocates `if not self: return not other` after the Boolean/NumberSymbol/mpf branches — the doc never reproduces that line or its ordering as code). The hidden test name (test_zero_not_false), its file path (sympy/core/tests/test_numbers.py), and the test-code form never appear. Req 1.2's S.true clause is a generalization over Boolean (the test only checks S.false), so it is not test-parametrization mirroring but genuine behavioral spec. No parametrization ids, no fix-invented identifiers, no verbatim gold lines. No semantic leakage beyond the public problem statement.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
