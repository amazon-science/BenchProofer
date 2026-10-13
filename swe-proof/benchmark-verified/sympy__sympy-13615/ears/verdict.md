# P2 adversarial audit — sympy__sympy-13615

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
Partial-fix candidate (drops definite members but keeps undetermined elements as bare FiniteSet members): Complement(FiniteSet(x,y,2), Interval(0,10)) -> FiniteSet(x,y) instead of Complement(FiniteSet(x,y), Interval(0,10), evaluate=False). Rejected by probes 1,2,5.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control -- Requirement 2.5 / 1.4.
Complement of {x, y, 2} against Interval(0,10): the interior number 2 is a
definite member (dropped); x,y are undetermined and must survive as an
UNEVALUATED complement against the interval. Result must equal
Complement(FiniteSet(x,y), Interval(0,10), evaluate=False).
Exit 0 iff that holds.
"""
from sympy import FiniteSet, Interval, Symbol, Complement

x, y = Symbol('x'), Symbol('y')
got = Complement(FiniteSet(x, y, 2), Interval(0, 10))
want = Complement(FiniteSet(x, y), Interval(0, 10), evaluate=False)
print("got :", got)
print("want:", want)
ok = (got == want)
print("equal:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Requirement 1.4 / 2.1 -- undetermined element must NOT appear as an explicit
FiniteSet member; it must live inside an unevaluated Complement.
Take {x, 1} against Interval(0,10): 1 is a definite member (dropped), x is
undetermined. Result must be exactly Complement(FiniteSet(x), Interval(0,10),
evaluate=False) -- x is NOT a bare confirmed member.
"""
from sympy import FiniteSet, Interval, Symbol, Complement

x = Symbol('x')
got = Complement(FiniteSet(x, 1), Interval(0, 10))
want = Complement(FiniteSet(x), Interval(0, 10), evaluate=False)
print("got :", got, type(got))
print("want:", want)
# x must NOT be asserted as a definite non-member (bare FiniteSet {x})
bad = FiniteSet(x)
print("equals bare {x} (WRONG):", got == bad)
ok = (got == want) and (got != bad)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Requirement 3.1 / 2.2 -- all definite non-members: result equals `other`
unchanged, with NO residual unevaluated complement term.
{-1, 20} against Interval(0,10): both outside -> FiniteSet(-1, 20).
"""
from sympy import FiniteSet, Interval, Complement

got = Complement(FiniteSet(-1, 20), Interval(0, 10))
want = FiniteSet(-1, 20)
print("got :", got, type(got))
print("want:", want)
ok = (got == want) and got.func.__name__ == 'FiniteSet'
print("is FiniteSet:", got.func.__name__ == 'FiniteSet')
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Requirement 2.3 / 3.2 / 1.2 -- every element a definite member -> EmptySet.
{2, 5} against Interval(0,10): both inside -> S.EmptySet (not empty FiniteSet,
not an empty unevaluated complement).
"""
from sympy import FiniteSet, Interval, Complement, S

got = Complement(FiniteSet(2, 5), Interval(0, 10))
print("got :", got, type(got))
ok = (got == S.EmptySet)
print("is EmptySet:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Requirement 2.1 / 2.4 -- MIXED case: confirmed non-members combine with an
unevaluated complement of the undetermined ones, and confirmed non-members keep
canonical FiniteSet form (dedup/order).
{x, y, 2, -1, 20} against Interval(0,10):
  2 -> member (drop); -1,20 -> non-members; x,y -> undetermined.
Result must equal Union(FiniteSet(-1,20), Complement(FiniteSet(x,y),
Interval(0,10), evaluate=False)).
"""
from sympy import FiniteSet, Interval, Symbol, Complement, Union

x, y = Symbol('x'), Symbol('y')
got = Complement(FiniteSet(x, y, 2, -1, 20), Interval(0, 10))
want = Union(FiniteSet(-1, 20),
             Complement(FiniteSet(x, y), Interval(0, 10), evaluate=False))
print("got :", got)
print("want:", want)
ok = (got == want)
print("equal:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Requirement 3.3 -- non-finite second operand behavior unchanged.
Interval minus reals -> EmptySet; a nested/interval complement stays as before.
"""
from sympy import Interval, S, Complement, FiniteSet

r1 = Complement(Interval(0, 1), S.Reals)
print("Interval - Reals =", r1)
# Interval complement against reals should be EmptySet
c1 = (r1 == S.EmptySet)

# Complement of interval against a finite set: e.g. Reals - {1}
r2 = Complement(S.Reals, FiniteSet(1))
print("Reals - {1} =", r2)
c2 = (1 not in r2) and (S(2) in r2)

print("c1,c2 =", c1, c2)
raise SystemExit(0 if (c1 and c2) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control -- Requirement 2.5 / 1.4.
Complement of {x, y, 2} against Interval(0,10): the interior number 2 is a
definite member (dropped); x,y are undetermined and must survive as an
UNEVALUATED complement against the interval. Result must equal
Complement(FiniteSet(x,y), Interval(0,10), evaluate=False).
Exit 0 iff that holds.
"""
from sympy import FiniteSet, Interval, Symbol, Complement

x, y = Symbol('x'), Symbol('y')
got = Complement(FiniteSet(x, y, 2), Interval(0, 10))
want = Complement(FiniteSet(x, y), Interval(0, 10), evaluate=False)
print("got :", got)
print("want:", want)
ok = (got == want)
print("equal:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree. Positive controls probe_1 (Req 2.5/1.4), probe_2 (Req 1.4/2.1), probe_5 (Req 2.1/2.4 mixed) each FAIL at base and HOLD patched -> discriminating power confirmed. Regression probes probe_3 (Req 3.1/2.2 all non-members unchanged), probe_4 (Req 2.3/3.2 all members -> EmptySet), probe_6 (Req 3.3 non-finite second operand unchanged) HOLD on both base and patched. Candidate patch weak.diff applies at base and encodes the lazy reading that fixes definite-member dropping but leaves undetermined elements as confirmed members: it is REJECTED by probes 1,2,5 (each requires the unevaluated Complement wrapper) while passing 3,4,6 -> suite discriminates wrong implementations. No requirements-conforming alternative found; requirements faithfully pin the gold behavior.

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
Partial-fix candidate (drops definite members but keeps undetermined elements as bare FiniteSet members): Complement(FiniteSet(x,y,2), Interval(0,10)) -> FiniteSet(x,y) instead of Complement(FiniteSet(x,y), Interval(0,10), evaluate=False). Rejected by probes 1,2,5.
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
"""Positive control -- Requirement 2.5 / 1.4.
Complement of {x, y, 2} against Interval(0,10): the interior number 2 is a
definite member (dropped); x,y are undetermined and must survive as an
UNEVALUATED complement against the interval. Result must equal
Complement(FiniteSet(x,y), Interval(0,10), evaluate=False).
Exit 0 iff that holds.
"""
from sympy import FiniteSet, Interval, Symbol, Complement

x, y = Symbol('x'), Symbol('y')
got = Complement(FiniteSet(x, y, 2), Interval(0, 10))
want = Complement(FiniteSet(x, y), Interval(0, 10), evaluate=False)
print("got :", got)
print("want:", want)
ok = (got == want)
print("equal:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree. Positive controls probe_1 (Req 2.5/1.4), probe_2 (Req 1.4/2.1), probe_5 (Req 2.1/2.4 mixed) each FAIL at base and HOLD patched -> discriminating power confirmed. Regression probes probe_3 (Req 3.1/2.2 all non-members unchanged), probe_4 (Req 2.3/3.2 all members -> EmptySet), probe_6 (Req 3.3 non-finite second operand unchanged) HOLD on both base and patched. Candidate patch weak.diff applies at base and encodes the lazy reading that fixes definite-member dropping but leaves undetermined elements as confirmed members: it is REJECTED by probes 1,2,5 (each requires the unevaluated Complement wrapper) while passing 3,4,6 -> suite discriminates wrong implementations. No requirements-conforming alternative found; requirements faithfully pin the gold behavior.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** R1.1-1.5 (three-valued classification, only boolean-True = member) match the ternary_sift/`contains in [True,False]` logic exactly. R2.1-2.3/2.5 match the Union(FiniteSet(sifted[False]), Complement(...) if sifted[None] else EmptySet) assembly. R3.3/3.4 (non-FiniteSet operands, dependent ops) are correctly preserved since the patch touches only the FiniteSet branch. Requirements pin the changed behavior, not a narrow slice. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document's behavioral requirements are all derivable from the PUBLIC problem_statement, which shows Complement(FiniteSet(x,y,2), Interval(-10,10)) == {x,y} \\ [-10,10]. Req 2.5 restates this example abstractly ('two free symbols together with a number that lies strictly inside a numeric interval') without pinning the hidden test's concrete literals (-10,10,2). No gold-invented identifiers leak: the fix's helpers (sift, ternary_sift, sifted[None]) are never named — the doc uses generic 'three-valued classification' prose that translates behavior, which is the intended purpose. The single hidden FAIL_TO_PASS assertion (test_Complement) matches the public example, so there is no case-enumeration mirroring test parametrization. Test names/paths are not present. ComplexRegion (line 14) originates from hints_text, not the test_patch, so it is not a hidden-test leak. Module/function names (sympy/sets/sets.py, Set._complement, FiniteSet, Set.contains) are legitimate localization.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
