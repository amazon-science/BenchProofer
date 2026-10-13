# P2 adversarial audit — sympy__sympy-16450

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req 1.3 (positive control): finite=True symbol -> replacement reports
finite=True, infinite=False, positive=True."""
import sys
from sympy import posify, Symbol

k = Symbol('k', finite=True)
eq, rep = posify(k)
a = eq.assumptions0
print("assumptions0 =", a)
ok = a.get('finite') is True and a.get('infinite') is False and a.get('positive') is True
print("finite/infinite/positive ok:", ok)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.4: replacement's full resolved assumptions == a fresh symbol declared
with original's declared assumptions plus positive=True. Test with finite=True."""
import sys
from sympy import posify, Symbol

k = Symbol('k', finite=True)
eq, rep = posify(k)
expected = Symbol('_k', positive=True, finite=True).assumptions0
got = eq.assumptions0
print("got     =", got)
print("expected=", expected)
ok = got == expected
print("exact match:", ok)
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.2: various declared assumptions (integer, rational, even, odd, prime)
are preserved on the replacement symbol."""
import sys
from sympy import posify, Symbol

cases = [
    ('integer', dict(integer=True)),
    ('rational', dict(rational=True)),
    ('even', dict(even=True)),
    ('odd', dict(odd=True)),
    ('prime', dict(prime=True)),
]
allok = True
for name, kw in cases:
    s = Symbol('s', **kw)
    eq, rep = posify(s)
    a = eq.assumptions0
    val = a.get(name)
    print(name, "->", val, "positive=", a.get('positive'))
    if val is not True or a.get('positive') is not True:
        allok = False
sys.exit(0 if allok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 2 & 5.2: only sign-undetermined symbols replaced; determined ones remain
and are not in mapping. Req 3: name preserved, round-trip restoration."""
import sys
from sympy import posify, Symbol, symbols

x = symbols('x')
p = symbols('p', positive=True)
n = symbols('n', negative=True)
orig = [x, n, p]
modified, reps = posify(orig)
print("modified:", modified)
print("reps:", reps)
ok = str(modified) == '[_x, n, p]'
# determined symbols not in mapping (values are originals)
ok = ok and set(reps.values()) == {x}
# round trip
ok = ok and [w.subs(reps) for w in modified] == orig
# name preserved
dummy = list(reps.keys())[0]
ok = ok and dummy.name == 'x'
print("all ok:", ok)
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 5.1: log(1/x) expands to -log(_x); round trip restores -log(x).
Req 3.1/3.2: two-element result, mapping restores original."""
import sys
from sympy import posify, log, Symbol
from sympy.abc import x

eq, rep = posify(1/x)
expanded = log(eq).expand()
print("log(posify(1/x)).expand() =", expanded)
restored = expanded.subs(rep)
print("restored =", restored)
ok = str(expanded) == '-log(_x)' and restored == -log(x)
# two-element result: expr + dict
ok = ok and isinstance(rep, dict)
print("ok:", ok)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 4: iterable of expressions; shared symbol replaced consistently with the
same dummy; assumption preservation applies within iterables."""
import sys
from sympy import posify, Symbol

# shared symbol with an assumption across two expressions
m = Symbol('m', integer=True)
res, reps = posify([1/m, 1 + m])
print("res:", res, "type:", type(res).__name__)
ok = isinstance(res, list)
# same dummy used in both
dummy = list(reps.keys())[0]
ok = ok and all(dummy in e.free_symbols for e in res)
# assumption preserved
a = dummy.assumptions0
print("dummy assumptions:", a)
ok = ok and a.get('integer') is True and a.get('positive') is True
# name preserved
ok = ok and dummy.name == 'm'
print("ok:", ok)
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
"""Req 1.4: replacement's full resolved assumptions == a fresh symbol declared
with original's declared assumptions plus positive=True. Test with finite=True."""
import sys
from sympy import posify, Symbol

k = Symbol('k', finite=True)
eq, rep = posify(k)
expected = Symbol('_k', positive=True, finite=True).assumptions0
got = eq.assumptions0
print("got     =", got)
print("expected=", expected)
ok = got == expected
print("exact match:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

posify assumption-preservation (sympy-16450). Probes vs patched/base/weak:
- probe_1 (Req1.3): finite=True -> replacement finite/infinite/positive. PATCHED HOLDS, BASE VIOLATED.
- probe_2 (Req1.4, POSITIVE CONTROL): full resolved assumptions == fresh Symbol(positive,finite). PATCHED HOLDS, BASE VIOLATED.
- probe_3 (Req1.2): integer/rational/even/odd/prime each preserved. PATCHED HOLDS, BASE VIOLATED, WEAK VIOLATED (rejects the finite-only patch).
- probe_4 (Req2/3/5.2 regression): only sign-undetermined replaced; determined not in mapping; round-trip; name preserved. HOLDS on patched & base (regression guard).
- probe_5 (Req5.1/3): log(1/x)->-log(_x), round-trip restore. HOLDS patched & base (regression guard).
- probe_6 (Req4): iterable, shared symbol -> same dummy, assumption (integer) preserved. PATCHED HOLDS, BASE VIOLATED, WEAK VIOLATED.
Weak candidate (Dummy with positive=True plus finite only when s.is_finite) is a requirements-plausible partial fix: it passes probes 1,2,5 but is REJECTED by probes 3 and 6 (non-finite assumptions like integer/rational/even/odd/prime dropped) — demonstrating the suite discriminates wrong implementations. Gold patch uses **s.assumptions0 and passes all probes. All 6 probes hold on patched tree; positive control (probe_2) discriminates (holds patched, fails base).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_2.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
"""Req 1.4: replacement's full resolved assumptions == a fresh symbol declared
with original's declared assumptions plus positive=True. Test with finite=True."""
import sys
from sympy import posify, Symbol

k = Symbol('k', finite=True)
eq, rep = posify(k)
expected = Symbol('_k', positive=True, finite=True).assumptions0
got = eq.assumptions0
print("got     =", got)
print("expected=", expected)
ok = got == expected
print("exact match:", ok)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

posify assumption-preservation (sympy-16450). Probes vs patched/base/weak:
- probe_1 (Req1.3): finite=True -> replacement finite/infinite/positive. PATCHED HOLDS, BASE VIOLATED.
- probe_2 (Req1.4, POSITIVE CONTROL): full resolved assumptions == fresh Symbol(positive,finite). PATCHED HOLDS, BASE VIOLATED.
- probe_3 (Req1.2): integer/rational/even/odd/prime each preserved. PATCHED HOLDS, BASE VIOLATED, WEAK VIOLATED (rejects the finite-only patch).
- probe_4 (Req2/3/5.2 regression): only sign-undetermined replaced; determined not in mapping; round-trip; name preserved. HOLDS on patched & base (regression guard).
- probe_5 (Req5.1/3): log(1/x)->-log(_x), round-trip restore. HOLDS patched & base (regression guard).
- probe_6 (Req4): iterable, shared symbol -> same dummy, assumption (integer) preserved. PATCHED HOLDS, BASE VIOLATED, WEAK VIOLATED.
Weak candidate (Dummy with positive=True plus finite only when s.is_finite) is a requirements-plausible partial fix: it passes probes 1,2,5 but is REJECTED by probes 3 and 6 (non-finite assumptions like integer/rational/even/odd/prime dropped) — demonstrating the suite discriminates wrong implementations. Gold patch uses **s.assumptions0 and passes all probes. All 6 probes hold on patched tree; positive control (probe_2) discriminates (holds patched, fails base).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Ran the probe on both gold-patched (exit 0, ALL OK) and base (exit 1, AssertionError is_finite None). Requirements do not overreach: they don't mandate any behavior absent from the patch, don't forbid preserved behaviors, and pin the changed behavior (assumption preservation on the positive dummy) rather than a narrow branch/helper slice. G-HYGIENE/G-LEAK/G-RESOLVE all pass in meta.json.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to posify in sympy/simplify/simplify.py (legitimate) and translates the fix into behavioral requirements. Every enumeration that could look test-shaped is in fact derivable from the PUBLIC problem_statement: it already prints xp._assumptions (positive/real/hermitian/imaginary/negative/nonnegative/nonzero/zero/complex/nonpositive/commutative), the finite=True / infinite=False example, and the explicit candidate list 'integer, rational, prime, even, odd'. AC 1.2 and 1.4's property lists mirror that public material, not the test parametrization. The hidden test (test_posify) contributes only an assumptions0 equality assertion for a finite=True symbol named k; the requirements describe this behaviorally ('resolved assumptions SHALL report finite as True and infinite as False') without quoting the dict literal, the assumptions0 method, the test/function name, the symbol name, or the gold line Dummy(s.name, positive=True, **s.assumptions0). No test path/name/id, no verbatim gold/test code, no fix-invented identifier is transmitted.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
