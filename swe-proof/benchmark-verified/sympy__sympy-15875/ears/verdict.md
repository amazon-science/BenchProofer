# P2 adversarial audit — sympy__sympy-15875

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
# Req 1.1 / positive control: sum of purely-imaginary term + squared complex
# term that expands to its negation cancels to zero => is_zero must be None, not False.
from sympy import I
e = -2*I + (1 + I)**2   # (1+I)**2 = 2I ; sum = 0 but unsimplified
v = e.is_zero
print("expr =", e, " is_zero =", v)
import sys
sys.exit(0 if (v is None) else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 2.5 (nz==0 branch): sum of exactly one purely-imaginary summand and no
# nonzero-real anchor => _eval_is_zero returns None (previously False).
from sympy import I, Symbol
x = Symbol('x', imaginary=True)  # purely imaginary
from sympy.core.add import Add
e = Add(x, evaluate=False)
# better: a genuine multi-term case with no real nonzero. Use im + im_or_z.
y = Symbol('y', imaginary=True)
e2 = x + y   # two purely imaginary; nz empty
r = e2._eval_is_zero()
print("x+y (both imaginary) _eval_is_zero =", r)
import sys
sys.exit(0 if r is None else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 2.6 (im==1) / 2.7 regression: known-nonzero-real anchors give correct verdicts.
from sympy import Symbol, I
from sympy.core.add import Add
import sys
ok = True
a = Symbol('a', real=True, nonzero=True)
# 2.7: nz subsum definitely nonzero -> False.  a + a is 2a (nonzero)
e = Add(a, a)
r = e._eval_is_zero()
print("Add(a,a) _eval_is_zero =", r)
ok &= (r is False)
# 2.6 im==1: nz subsum zero + exactly one imaginary summand -> False.
# Build unevaluated so a + (-a) does not cancel structurally.
im = Symbol('im', imaginary=True)
e2 = Add(a, -a, im, evaluate=False)
print("Add(a,-a,im) args =", e2.args)
r2 = e2._eval_is_zero()
print("Add(a,-a,im) _eval_is_zero =", r2)
ok &= (r2 is False)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 2.4 & 3: all-zero-real sum -> True; and general regressions preserved.
from sympy import Symbol, Integer, I, sqrt
import sys
ok = True
# 2.4: sum of real terms known zero -> True
z1 = Symbol('z1', zero=True)
z2 = Symbol('z2', zero=True)
e = z1 + z2
r = e._eval_is_zero()
print("z1+z2 (both zero) _eval_is_zero =", r)
ok &= (r is True)
# Req 3 regression: ordinary nonzero real number sum
print("(2+3).is_zero =", (Integer(2)+Integer(3)).is_zero)
ok &= ((Integer(2)+Integer(3)).is_zero is False)
# real symbol undecidable -> None (2.2)
x = Symbol('x', real=True)
r2 = (x + 1)._eval_is_zero()
print("(x+1) real undecidable _eval_is_zero =", r2)
ok &= (r2 is None)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 1.2 downstream + soundness: matrix rank corruption case from the bug report.
# Also verify observable is_zero None for the canceling complex sum, and that a
# genuinely-nonzero complex sum still reads correctly (not over-relaxed).
from sympy import I, Matrix, Symbol
import sys
ok = True
# The classic failing matrix: rank should be computable / correct (not crash into wrong).
# From issue 15872: Matrix with entries producing the canceling Add.
q = Symbol('q', real=True)
# Simpler: verify observable property soundness on canceling sum
e = -2*I + (1+I)**2
print("observable is_zero(-2I+(1+I)**2) =", e.is_zero)
ok &= (e.is_zero is None)
# genuinely nonzero: 3*I + 5 (nonzero real anchor + imaginary) -> not True/None wrongly
f = 5 + 3*I
print("(5+3I).is_zero =", f.is_zero)
ok &= (f.is_zero is False)
# a real nonzero sum still False
print("(1+1).is_zero =", (1+Symbol('one',zero=False,real=True)).is_zero if False else (Symbol('p',positive=True)+Symbol('q2',positive=True)).is_zero)
ok &= ((Symbol('p',positive=True)+Symbol('q2',positive=True)).is_zero is False)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.1 / positive control: sum of purely-imaginary term + squared complex
# term that expands to its negation cancels to zero => is_zero must be None, not False.
from sympy import I
e = -2*I + (1 + I)**2   # (1+I)**2 = 2I ; sum = 0 but unsimplified
v = e.is_zero
print("expr =", e, " is_zero =", v)
import sys
sys.exit(0 if (v is None) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix: sympy/core/add.py Add._eval_is_zero changed `if len(nz) == len(self.args)` to `if len(nz) == 0 or len(nz) == len(self.args): return None`, so a sum with no known-nonzero-real anchor stays undecided (None) instead of falling through to the possibly-`False` branch.

Probes (all HOLD on gold-patched tree; env: swebench-lean conda python):
- probe_1 (Req 1.1, POSITIVE CONTROL): -2*I + (1+I)**2 cancels to 0 unsimplified; observable is_zero must be None. HOLDS patched, VIOLATED at base (exit 1: base returned False) => prepatch reproduced, discriminates.
- probe_2 (Req 2.5, nz==0 branch): Add of two purely-imaginary symbols x+y => _eval_is_zero None. HOLDS.
- probe_3 (Req 2.6 im==1 / 2.7 regression): Add(a,a) (nonzero real subsum) => False; Add(a,-a,im, evaluate=False) (nz subsum zero + one imaginary) => False. HOLDS (needed evaluate=False so terms don't structurally cancel).
- probe_4 (Req 2.4 & Req 3): two zero-real symbols => True; (2+3).is_zero False; (x+1) real-undecidable _eval_is_zero None. HOLDS.
- probe_5 (Req 1.2 downstream/soundness): observable is_zero of canceling complex sum None; 5+3I is_zero False; sum of two positives is_zero False. HOLDS.

Candidate wrong patch (weak.diff, applies at base_commit): only guards the pure-real empty-nz case (`len(nz)==0 and im==0`), leaving sums with imaginary/possibly-imaginary summands returning the old wrong False. Under it probes 1, 2, and 5 are VIOLATED (probes 3,4 hold) => the suite discriminates this partial fix. No requirements-conforming candidate found that would fail the hidden tests.

Verdict SOUND: >=5 distinct probes covering behavioral SHALLs (Req 1.1/1.2, Req 2.2/2.4/2.5/2.6/2.7) and Req 3 regressions all hold on the patched tree; positive control discriminates base vs patched; a plausible partial fix is rejected by the suite.

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
# Req 1.1 / positive control: sum of purely-imaginary term + squared complex
# term that expands to its negation cancels to zero => is_zero must be None, not False.
from sympy import I
e = -2*I + (1 + I)**2   # (1+I)**2 = 2I ; sum = 0 but unsimplified
v = e.is_zero
print("expr =", e, " is_zero =", v)
import sys
sys.exit(0 if (v is None) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix: sympy/core/add.py Add._eval_is_zero changed `if len(nz) == len(self.args)` to `if len(nz) == 0 or len(nz) == len(self.args): return None`, so a sum with no known-nonzero-real anchor stays undecided (None) instead of falling through to the possibly-`False` branch.

Probes (all HOLD on gold-patched tree; env: swebench-lean conda python):
- probe_1 (Req 1.1, POSITIVE CONTROL): -2*I + (1+I)**2 cancels to 0 unsimplified; observable is_zero must be None. HOLDS patched, VIOLATED at base (exit 1: base returned False) => prepatch reproduced, discriminates.
- probe_2 (Req 2.5, nz==0 branch): Add of two purely-imaginary symbols x+y => _eval_is_zero None. HOLDS.
- probe_3 (Req 2.6 im==1 / 2.7 regression): Add(a,a) (nonzero real subsum) => False; Add(a,-a,im, evaluate=False) (nz subsum zero + one imaginary) => False. HOLDS (needed evaluate=False so terms don't structurally cancel).
- probe_4 (Req 2.4 & Req 3): two zero-real symbols => True; (2+3).is_zero False; (x+1) real-undecidable _eval_is_zero None. HOLDS.
- probe_5 (Req 1.2 downstream/soundness): observable is_zero of canceling complex sum None; 5+3I is_zero False; sum of two positives is_zero False. HOLDS.

Candidate wrong patch (weak.diff, applies at base_commit): only guards the pure-real empty-nz case (`len(nz)==0 and im==0`), leaving sums with imaginary/possibly-imaginary summands returning the old wrong False. Under it probes 1, 2, and 5 are VIOLATED (probes 3,4 hold) => the suite discriminates this partial fix. No requirements-conforming candidate found that would fail the hidden tests.

Verdict SOUND: >=5 distinct probes covering behavioral SHALLs (Req 1.1/1.2, Req 2.2/2.4/2.5/2.6/2.7) and Req 3 regressions all hold on the patched tree; positive control discriminates base vs patched; a plausible partial fix is rejected by the suite.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch is the one-line guard `len(nz) == 0 or len(nz) == len(self.args): return None` in Add._eval_is_zero (add.py). Verified patched source in-image matches the requirement text clause-by-clause. Probes: fix obs=None/_eval=None; pos+pos _eval=None/obs=False; (2,-2,I) _eval=False; (2,3,I) _eval=False; base commit gives fix obs=False/_eval=False, pos+pos obs=False. The requirements pin the changed observable behavior (Req 1) and the full _eval return contract (Req 2) at the correct boundary; nothing invented, nothing forbidden that the code does, nothing mandated that it lacks. Note: G-PANEL-2 gate stamp in meta.json (fail) conflated the observable and method boundaries and misnumbered 2.5 as 2.6 — that stamp is unreliable; the spec itself is faithful.

Counterexample / evidence:

```
The prior UNFAITHFUL verdict's two counterexamples are misreadings, not real divergences. (a) Add(pos,pos): panel cited it against 'Req 2.6' reading the OBSERVABLE is_zero (=False). But Req 2 governs the _eval_is_zero RETURN VALUE, which is None here (engine refines to False via is_positive); and this input is Req 2.5 (nz==total -> None), not 2.6 — code returns None, matching. (b) Add(0,I): panel cited it against Req 1.1, but Add(0,I) collapses to ImaginaryUnit (not an Add) and does NOT match Req 1.1's antecedent (a purely-imaginary term plus a squared complex term whose expansion negates it). I is genuinely nonzero so is_zero=False is a correct definite; Req 1.2 only forbids WRONG definites. Base==patched confirms these are unchanged sound answers, consistent with (not contradicting) the requirements.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The only concrete case in the doc (Req 1.1: 'a sum of a purely-imaginary term and a squared complex term whose expansion is the negation of that imaginary term') is a paraphrase of the PUBLIC problem_statement example `e = -2*I + (1 + I)**2`, whose expected `is_zero` result (None, not False) and matrix-rank motivation are also public. No hidden-test artifacts leak: no test function/file names (test_Add_is_zero, test_arit.py), no parametrization ids (the F2P test is a single non-parametrized assertion), no quoted test code, and no fix-invented identifiers. Naming Add._eval_is_zero / sympy/core/add.py is legitimate localization (also public via hints_text link). Requirement 2's category enumeration and the 'zero or equal to total' condition (Req 2.5) describe the pre-existing _eval_is_zero algorithm and translate the one-line gold edit `if len(nz) == 0 or len(nz) == len(self.args): return None` into behavioral prose rather than transmitting the patch line or reconstructing the tests. `nz` is a pre-existing local variable in the source, not fix-invented. Behavioral translation is the intended function of the spec.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
