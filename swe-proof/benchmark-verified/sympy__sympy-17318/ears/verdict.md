# P2 adversarial audit — sympy__sympy-17318

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Req 2.2 / 3.2 positive control: _sqrt_match(4 + I) returns [] (no IndexError).
At base this raises IndexError inside _split_gcd."""
import sys
from sympy import S
from sympy.simplify.sqrtdenest import _sqrt_match

I = S.ImaginaryUnit
try:
    res = _sqrt_match(4 + I)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("_sqrt_match(4 + I) =", res)
sys.exit(0 if res == [] else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 3.2 / 3.1: sqrtdenest on an expr triggering surd matching on a sum with
a non-positive-rational square completes without exception and returns unchanged.
The hint expression `3 - sqrt(2)*sqrt(4 + I) + 3*I` does not auto-simplify."""
import sys
from sympy import sqrt, S
from sympy.simplify.sqrtdenest import sqrtdenest

I = S.ImaginaryUnit
e = 3 - sqrt(2)*sqrt(4 + I) + 3*I
try:
    res = sqrtdenest(e)
except Exception as ex:
    print("RAISED:", type(ex).__name__, ex)
    sys.exit(1)
print("sqrtdenest(e) =", res)
print("e            =", e)
sys.exit(0 if res == e else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 3.3: an input that auto-simplifies during denesting returns the simplified
value. (3 - sqrt(2)*sqrt(4 + 3*I) + 3*I)/2 auto-evaluates to I."""
import sys
from sympy import sqrt, S
from sympy.simplify.sqrtdenest import sqrtdenest

I = S.ImaginaryUnit
try:
    res = sqrtdenest((3 - sqrt(2)*sqrt(4 + 3*I) + 3*I)/2)
except Exception as ex:
    print("RAISED:", type(ex).__name__, ex)
    sys.exit(1)
print("result =", res)
sys.exit(0 if res == I else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 1.4 / 4.4: real surd sums still delegate to fast path and return the same
decomposition triple. _sqrt_match on a real surd sum must give the split_surds
result. Use p = 2*sqrt(2) + 3*sqrt(3) style; compare against split_surds directly."""
import sys
from sympy import sqrt, S
from sympy.simplify.sqrtdenest import _sqrt_match
from sympy.simplify.radsimp import split_surds

# a sum whose every addend square is a positive rational
p = 2 + sqrt(2) + sqrt(3)   # squares: 4, 2, 3 all positive rational
try:
    r, b, a = split_surds(p)
    expected = [a, b, r]
    got = _sqrt_match(p)
except Exception as ex:
    print("RAISED:", type(ex).__name__, ex)
    sys.exit(1)
print("split_surds triple:", expected)
print("_sqrt_match       :", got)
sys.exit(0 if got == expected else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 4.1: established real denesting results preserved.
sqrt(5 + 2*sqrt(6)) -> sqrt(2)+sqrt(3); and difference/sum regression case."""
import sys
from sympy import sqrt
from sympy.simplify.sqrtdenest import sqrtdenest

r2, r3, r6 = sqrt(2), sqrt(3), sqrt(6)
checks = []
checks.append((sqrtdenest(sqrt(5 + 2*r6)), r2 + r3))
# sqrt_ratcomb regression from the test file
checks.append((sqrtdenest(sqrt(1 + r3) + sqrt(3 + 3*r3) - sqrt(10 + 6*r3)), 0))
ok = True
for got, exp in checks:
    print("got:", got, "| expected:", exp)
    if got != exp:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 1.3 + 2.1: an addend whose square is a NON-positive rational must route to
the general path, not the fast surd path. p = 2 + 3*I: squares 4 (pos rat) and
-9 (neg rat); no sqrt structure -> depth 0 -> []. At base this crashes IndexError
(fast path entered with empty surds list)."""
import sys
from sympy import S
from sympy.simplify.sqrtdenest import _sqrt_match

I = S.ImaginaryUnit
try:
    res = _sqrt_match(2 + 3*I)
except Exception as ex:
    print("RAISED:", type(ex).__name__, ex)
    sys.exit(1)
print("_sqrt_match(2 + 3*I) =", res)
sys.exit(0 if res == [] else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Req 2.2 / 3.2 positive control: _sqrt_match(4 + I) returns [] (no IndexError).
At base this raises IndexError inside _split_gcd."""
import sys
from sympy import S
from sympy.simplify.sqrtdenest import _sqrt_match

I = S.ImaginaryUnit
try:
    res = _sqrt_match(4 + I)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("_sqrt_match(4 + I) =", res)
sys.exit(0 if res == [] else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree; each encodes a requirement criterion:
- probe_1 (Req 2.2/3.2, POSITIVE CONTROL): _sqrt_match(4 + I) == []. Base: IndexError in _split_gcd. Patched: []. DISCRIMINATES (base FAIL -> patched HOLD).
- probe_2 (Req 3.1/3.2): sqrtdenest(3 - sqrt(2)*sqrt(4 + I) + 3*I) completes without exception and returns the expr unchanged (this expr does NOT auto-simplify). Base: IndexError. Patched: unchanged. DISCRIMINATES.
- probe_3 (Req 3.3): sqrtdenest((3 - sqrt(2)*sqrt(4 + 3*I) + 3*I)/2) == I (input auto-simplifies to I). Holds on both trees (auto-eval), so non-discriminating but a valid criterion check.
- probe_4 (Req 1.4/4.4): real surd sum (2 + sqrt(2) + sqrt(3), all addend squares positive rational) still delegates to fast split_surds path; _sqrt_match triple == split_surds triple [sqrt(3)+2, 1, 2].
- probe_5 (Req 4.1): established real denests preserved: sqrt(5+2*sqrt6)->sqrt2+sqrt3; sqrt(1+r3)+sqrt(3+3r3)-sqrt(10+6r3)->0.
- probe_6 (Req 1.3/2.1, DISCRIMINATES): _sqrt_match(2 + 3*I) (squares 4 pos-rat and -9 neg-rat, no sqrt structure) == []. Base: IndexError. Patched: [].

Initial probe_6 variant used sqrt(2)+I which legitimately matches [I,1,2] via the general path (it has a real surd) — corrected to 2+3*I which has no surd and must return [].

### Candidate patches
- docs_only.diff (lazy fix = only the radsimp.py docstring edits, omitting the sqrtdenest.py guard): REJECTED by probes 1, 2, 6 (still raises IndexError). Demonstrates the suite discriminates a requirements-underconforming fix.
- tryexcept.diff (guard-by-catching-IndexError, the maintainer-discouraged approach): passes ALL 6 probes AND produces the same observable results, so it is a genuinely CORRECT alternative fix that would resolve test_issue_12420 — NOT a too-weak exposure. No requirements-conforming patch was found that fails the hidden tests.

Conclusion: >=5 probes hold on patched; positive control discriminates (FAIL at base, HOLD patched, prepatch_reproduced=true); >=1 candidate exercised and REJECTED (docs_only). No violation on the gold tree; no probe-conforming patch that fails to resolve. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected 1 of the 2: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. The other 1 was not rejected by the suite. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
"""Req 2.2 / 3.2 positive control: _sqrt_match(4 + I) returns [] (no IndexError).
At base this raises IndexError inside _split_gcd."""
import sys
from sympy import S
from sympy.simplify.sqrtdenest import _sqrt_match

I = S.ImaginaryUnit
try:
    res = _sqrt_match(4 + I)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    sys.exit(1)
print("_sqrt_match(4 + I) =", res)
sys.exit(0 if res == [] else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes, all HOLD on gold-patched tree; each encodes a requirement criterion:
- probe_1 (Req 2.2/3.2, POSITIVE CONTROL): _sqrt_match(4 + I) == []. Base: IndexError in _split_gcd. Patched: []. DISCRIMINATES (base FAIL -> patched HOLD).
- probe_2 (Req 3.1/3.2): sqrtdenest(3 - sqrt(2)*sqrt(4 + I) + 3*I) completes without exception and returns the expr unchanged (this expr does NOT auto-simplify). Base: IndexError. Patched: unchanged. DISCRIMINATES.
- probe_3 (Req 3.3): sqrtdenest((3 - sqrt(2)*sqrt(4 + 3*I) + 3*I)/2) == I (input auto-simplifies to I). Holds on both trees (auto-eval), so non-discriminating but a valid criterion check.
- probe_4 (Req 1.4/4.4): real surd sum (2 + sqrt(2) + sqrt(3), all addend squares positive rational) still delegates to fast split_surds path; _sqrt_match triple == split_surds triple [sqrt(3)+2, 1, 2].
- probe_5 (Req 4.1): established real denests preserved: sqrt(5+2*sqrt6)->sqrt2+sqrt3; sqrt(1+r3)+sqrt(3+3r3)-sqrt(10+6r3)->0.
- probe_6 (Req 1.3/2.1, DISCRIMINATES): _sqrt_match(2 + 3*I) (squares 4 pos-rat and -9 neg-rat, no sqrt structure) == []. Base: IndexError. Patched: [].

Initial probe_6 variant used sqrt(2)+I which legitimately matches [I,1,2] via the general path (it has a real surd) — corrected to 2+3*I which has no surd and must return [].

### Candidate patches
- docs_only.diff (lazy fix = only the radsimp.py docstring edits, omitting the sqrtdenest.py guard): REJECTED by probes 1, 2, 6 (still raises IndexError). Demonstrates the suite discriminates a requirements-underconforming fix.
- tryexcept.diff (guard-by-catching-IndexError, the maintainer-discouraged approach): passes ALL 6 probes AND produces the same observable results, so it is a genuinely CORRECT alternative fix that would resolve test_issue_12420 — NOT a too-weak exposure. No requirements-conforming patch was found that fails the hidden tests.

Conclusion: >=5 probes hold on patched; positive control discriminates (FAIL at base, HOLD patched, prepatch_reproduced=true); >=1 candidate exercised and REJECTED (docs_only). No violation on the gold tree; no probe-conforming patch that fails to resolve. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeling boundary is correct: requirements pin the changed observable behavior of _sqrt_match (and transitively sqrtdenest), which is precisely the single behavioral hunk in the diff. No requirement mandates behavior absent from the patch, forbids behavior present, or invents new behavior. Probes run in the instance image confirm base raises IndexError on 4+3*I / 3+I and the full issue expression, while the patched tree returns [] / the expression unchanged. Verdict FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change to _sqrt_match/split_surds/_split_gcd/sqrtdenest in sqrtdenest.py and radsimp.py, and translate the guard behavior (delegate to fast surd path only when every addend's square is a positive rational, else use general depth path) into acceptance criteria. Every function/file name, the repro expression, the IndexError, and the 'returned unchanged' behavior are all present in the PUBLIC problem_statement traceback and PR text. No hidden-only content is transmitted: the test name test_issue_12420, its file path, the literal assertions (_sqrt_match(4 + I) == [], sqrtdenest(...) == I, e == e), and the specific gold identifiers/docstring edits do not appear. The gold guard 'sq.is_Rational and sq.is_positive' invents no new identifier — it is a natural-language behavioral condition, and 'positive rational square' is the whole point of the spec, not a leak. Req 2.2 (rational + imaginary unit -> empty list) is the minimal natural bug case, not a quoted test; Req 3.3 (auto-simplifies to a simpler value) gestures at the '== I' outcome without stating the value. Req 4 regression items describe general denesting categories, not PASS_TO_PASS test names. No case enumeration mirrors the test parametrization (test uses single assertions, not parametrized ids).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
