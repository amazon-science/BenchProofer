# P2 adversarial audit — sympy__sympy-16597

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
# Positive control: Req2.2/Req4.4 — even symbol is finite (and integer)
from sympy import Symbol
m = Symbol('m', even=True)
print("even sym is_finite =", m.is_finite, "is_integer =", m.is_integer)
ok = (m.is_finite is True) and (m.is_integer is True)
import sys
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req1.1-1.4: rational/irrational/algebraic/transcendental imply finiteness (+ real/complex/not algebraic)
from sympy import Symbol
import sys
checks = []
r = Symbol('r', rational=True)
checks.append(("rational->finite", r.is_finite is True))
checks.append(("rational->real", r.is_real is True))
i = Symbol('i', irrational=True)
checks.append(("irrational->finite", i.is_finite is True))
checks.append(("irrational->real", i.is_real is True))
a = Symbol('a', algebraic=True)
checks.append(("algebraic->finite", a.is_finite is True))
checks.append(("algebraic->complex", a.is_complex is True))
t = Symbol('t', transcendental=True)
checks.append(("transcendental->finite", t.is_finite is True))
checks.append(("transcendental->complex", t.is_complex is True))
checks.append(("transcendental->not algebraic", t.is_algebraic is False))
for n,v in checks:
    print(n, "=", v)
sys.exit(0 if all(v for _,v in checks) else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req2: integer family finite. integer->finite,rational,real; odd/prime/composite->finite
from sympy import Symbol
import sys
checks = []
n = Symbol('n', integer=True)
checks.append(("integer->finite", n.is_finite is True))
checks.append(("integer->rational", n.is_rational is True))
checks.append(("integer->real", n.is_real is True))
o = Symbol('o', odd=True)
checks.append(("odd->finite", o.is_finite is True))
checks.append(("odd->integer", o.is_integer is True))
p = Symbol('p', prime=True)
checks.append(("prime->finite", p.is_finite is True))
c = Symbol('c', composite=True)
checks.append(("composite->finite", c.is_finite is True))
for k,v in checks: print(k,"=",v)
sys.exit(0 if all(v for _,v in checks) else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req3.3/3.4: S.Infinity and S.NegativeInfinity resolve number-class facts to False, keep real/complex/sign
from sympy import S
import sys
oo = S.Infinity
noo = S.NegativeInfinity
checks = []
for name,obj,sign in [("+oo",oo,"positive"),("-oo",noo,"negative")]:
    checks.append((name+" integer False", obj.is_integer is False))
    checks.append((name+" rational False", obj.is_rational is False))
    checks.append((name+" algebraic False", obj.is_algebraic is False))
    checks.append((name+" transcendental False", obj.is_transcendental is False))
    checks.append((name+" irrational False", obj.is_irrational is False))
    checks.append((name+" even False", obj.is_even is False))
    checks.append((name+" odd False", obj.is_odd is False))
    checks.append((name+" real True", obj.is_real is True))
    checks.append((name+" complex True", obj.is_complex is True))
    checks.append((name+" finite False", obj.is_finite is False))
    checks.append((name+" infinite True", obj.is_infinite is True))
# +oo specific: composite False, noninteger True
checks.append(("+oo composite False", oo.is_composite is False))
checks.append(("+oo noninteger True", oo.is_noninteger is True))
checks.append(("+oo positive True", oo.is_positive is True))
checks.append(("-oo negative True", noo.is_negative is True))
for k,v in checks: print(k,"=",v)
sys.exit(0 if all(v for _,v in checks) else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req5: negated bounded-class assumptions stay non-committal (finiteness unknown)
from sympy import Symbol
import sys
checks = []
e = Symbol('e', even=False)
checks.append(("even=False -> finite None", e.is_finite is None))
checks.append(("even=False -> integer None", e.is_integer is None))
o = Symbol('o', odd=False)
checks.append(("odd=False -> finite None", o.is_finite is None))
checks.append(("odd=False -> integer None", o.is_integer is None))
r = Symbol('r', rational=False)
checks.append(("rational=False -> finite None", r.is_finite is None))
checks.append(("rational=False -> real None", r.is_real is None))
i = Symbol('i', irrational=False)
checks.append(("irrational=False -> finite None", i.is_finite is None))
checks.append(("irrational=False -> real None", i.is_real is None))
for k,v in checks: print(k,"=",v)
sys.exit(0 if all(v for _,v in checks) else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req6 regression: concrete numbers unchanged + power rationality + NaN/zoo unchanged
from sympy import S, pi, E, I, Symbol, Integer, Rational, nan, zoo
import sys
checks = []
for num in [S.Zero, S.One, S.NegativeOne]:
    checks.append((str(num)+" integer", num.is_integer is True))
    checks.append((str(num)+" rational", num.is_rational is True))
    checks.append((str(num)+" real", num.is_real is True))
    checks.append((str(num)+" finite", num.is_finite is True))
r = Rational(3,7)
checks.append(("3/7 rational", r.is_rational is True))
checks.append(("3/7 finite", r.is_finite is True))
checks.append(("pi transcendental", pi.is_transcendental is True))
checks.append(("pi irrational", pi.is_irrational is True))
checks.append(("pi finite", pi.is_finite is True))
checks.append(("E transcendental", E.is_transcendental is True))
checks.append(("I imaginary", I.is_imaginary is True))
checks.append(("I complex", I.is_complex is True))
checks.append(("I finite", I.is_finite is True))
# NaN and zoo: no new definite finite/integer conclusions
checks.append(("nan integer not True", nan.is_integer is not True))
checks.append(("nan finite not True", nan.is_finite is not True))
checks.append(("zoo finite not True", zoo.is_finite is not True))
# Power rationality Req6.4: rational (nonzero) base, integer exponent, so not (0**neg) -> rational True
b = Symbol('b', rational=True, nonzero=True)
n = Symbol('n', integer=True)
checks.append(("nonzero-rational**integer rational", (b**n).is_rational is True))
checks.append(("2**3 rational", (Integer(2)**Integer(3)).is_rational is True))
fails = [k for k,v in checks if not v]
print("FAILS:", fails)
sys.exit(0 if not fails else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Positive control: Req2.2/Req4.4 — even symbol is finite (and integer)
from sympy import Symbol
m = Symbol('m', even=True)
print("even sym is_finite =", m.is_finite, "is_integer =", m.is_integer)
ok = (m.is_finite is True) and (m.is_integer is True)
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Probes vs requirements (all HOLD on gold-patched tree; all discriminate at base):
- probe_1 (POSITIVE CONTROL): Req2.2/4.4 even Symbol is_finite True & is_integer True. HOLDS patched, VIOLATED base.
- probe_2: Req1.1-1.4 rational/irrational->finite+real; algebraic->finite+complex; transcendental->finite+complex+not-algebraic. HOLDS patched, VIOLATED base.
- probe_3: Req2.1-2.5 integer->finite/rational/real; odd->finite/integer; prime->finite; composite->finite. HOLDS patched.
- probe_4: Req3.3/3.4 S.Infinity & S.NegativeInfinity number-class facts all False (integer/rational/algebraic/transcendental/irrational/even/odd), keep real/complex/finite=False/infinite=True; +oo composite False & noninteger True & positive; -oo negative. HOLDS patched, VIOLATED base.
- probe_5: Req5.1-5.4 negated bounded-class symbols (even=False/odd=False/rational=False/irrational=False) leave finite None and integer/real None. HOLDS patched.
- probe_6: Req6 regression: concrete numbers (0,1,-1,3/7,pi,E,I) number-class facts unchanged; NaN/zoo not newly finite/integer; Req6.4 power rationality (nonzero rational base ** integer exp -> rational True; 2**3 rational). HOLDS patched.

Probe fix note: initial probe_6 used a plain rational base for the power check; the engine correctly returns None there because is_zero is unknown (Req6.4 excludes 0**neg), so I constrained the base nonzero to match the requirement faithfully.

CANDIDATE PATCH (weak.diff): partial fix adding finiteness only to 'rational->real&finite' and 'algebraic->complex&finite' in core/assumptions.py, omitting the transcendental and irrational equivalences. It is REJECTED by probe_2 (transcendental/irrational symbols not finite) and probe_4 (+oo/-oo transcendental/irrational contrapositives not resolved to False) — demonstrating the suite discriminates a plausibly-wrong partial fix. This candidate would also fail the hidden F2P tests (test_infinity/test_neg_infinity/test_other_symbol). Note the runner truncates probe stdout after the first line; verdicts were read from exit codes.

Verdict SOUND: >=5 distinct probes covering behavioral SHALLs, boundary (infinities), negation non-commitment, and regression criteria all hold on patched; positive control discriminates patched-vs-base; and a requirements-partial alternative patch is rejected by the suite.

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
# Positive control: Req2.2/Req4.4 — even symbol is finite (and integer)
from sympy import Symbol
m = Symbol('m', even=True)
print("even sym is_finite =", m.is_finite, "is_integer =", m.is_integer)
ok = (m.is_finite is True) and (m.is_integer is True)
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Probes vs requirements (all HOLD on gold-patched tree; all discriminate at base):
- probe_1 (POSITIVE CONTROL): Req2.2/4.4 even Symbol is_finite True & is_integer True. HOLDS patched, VIOLATED base.
- probe_2: Req1.1-1.4 rational/irrational->finite+real; algebraic->finite+complex; transcendental->finite+complex+not-algebraic. HOLDS patched, VIOLATED base.
- probe_3: Req2.1-2.5 integer->finite/rational/real; odd->finite/integer; prime->finite; composite->finite. HOLDS patched.
- probe_4: Req3.3/3.4 S.Infinity & S.NegativeInfinity number-class facts all False (integer/rational/algebraic/transcendental/irrational/even/odd), keep real/complex/finite=False/infinite=True; +oo composite False & noninteger True & positive; -oo negative. HOLDS patched, VIOLATED base.
- probe_5: Req5.1-5.4 negated bounded-class symbols (even=False/odd=False/rational=False/irrational=False) leave finite None and integer/real None. HOLDS patched.
- probe_6: Req6 regression: concrete numbers (0,1,-1,3/7,pi,E,I) number-class facts unchanged; NaN/zoo not newly finite/integer; Req6.4 power rationality (nonzero rational base ** integer exp -> rational True; 2**3 rational). HOLDS patched.

Probe fix note: initial probe_6 used a plain rational base for the power check; the engine correctly returns None there because is_zero is unknown (Req6.4 excludes 0**neg), so I constrained the base nonzero to match the requirement faithfully.

CANDIDATE PATCH (weak.diff): partial fix adding finiteness only to 'rational->real&finite' and 'algebraic->complex&finite' in core/assumptions.py, omitting the transcendental and irrational equivalences. It is REJECTED by probe_2 (transcendental/irrational symbols not finite) and probe_4 (+oo/-oo transcendental/irrational contrapositives not resolved to False) — demonstrating the suite discriminates a plausibly-wrong partial fix. This candidate would also fail the hidden F2P tests (test_infinity/test_neg_infinity/test_other_symbol). Note the runner truncates probe stdout after the first line; verdicts were read from exit codes.

Verdict SOUND: >=5 distinct probes covering behavioral SHALLs, boundary (infinities), negation non-commitment, and regression criteria all hold on patched; positive control discriminates patched-vs-base; and a requirements-partial alternative patch is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the changed OBSERVABLE behavior (assumptions engine finiteness closure), matching the gold patch's edits to _assume_rules, ask_generated compiled facts, power._eval_is_rational early exit, and Idx infinity-bound tolerance. Modeling boundary is correct: it captures the full bounded-class -> finite change plus derived contrapositives on infinities, not a narrow single-branch slice. All probes exit 0 on the patched tree.

Counterexample / evidence:

```
zoo.is_finite=False in BOTH base and patched trees (verified with --base), so R6.3's 'leave number-class facts as before' is satisfied - it does not require None. And R6.4's power test returned None only for a fully-generic symbol whose precondition (not base-zero-with-negative-exponent) is UNKNOWN; when the precondition is known-true (e.g. exp nonnegative, or base nonzero) the early return fires and (base**exp).is_rational=True, exactly as R6.4 specifies ('IF ... it is not the case that the base is zero with a negative exponent, THEN report rational'). Both align with the patch's power.py fuzzy_not(fuzzy_and([exp.is_negative, base.is_zero])) guard.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe fix behavior in domain-standard SymPy assumption vocabulary (rational/irrational/algebraic/transcendental/finite/noninteger) and localize to the correct modules (core/assumptions.py, ask_generated.py, core/facts.py, core/power.py). No hidden-test artifacts transmitted: no test function names (test_infinity/test_neg_infinity/test_other_symbol/test_minmax_assumptions), no file paths, no parametrization ids, no quoted test or gold code, and no fix-invented identifiers (all names are pre-existing public API). Behavioral translations of the gold: Req 6.4 renders the power.py rationality guard (base rational & exp integer & not(base zero with negative exp)) as prose — a behavioral requirement, not verbatim code; Req 6.5 references two-arg min/max acceptance of an irrational-real symbol behaviorally. Closest tell: Req 3.3/3.4 enumerate the S.Infinity/S.NegativeInfinity fact tables closely tracking test_infinity/test_neg_infinity assertions, including the asymmetry of listing 'not composite' for +oo but omitting it for -oo (mirroring which test asserts composite). This is mildly test-shaped, but S.Infinity/S.NegativeInfinity are named public singletons whose observable assumption facts are legitimately describable, and the enumeration transmits no test identifiers and does not let a reader reconstruct the hidden test suite beyond the public problem statement's finiteness concern. Judged behavioral description, not test transmission.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
