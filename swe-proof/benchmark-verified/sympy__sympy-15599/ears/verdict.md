# P2 adversarial audit — sympy__sympy-15599

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
Weak candidate (weak.diff) drops the gold guard `(i % q is not S.Zero)`, reducing every integer factor in place including divisor-multiples. This zeroes coefficients prematurely: Mod(8*i/j, 4) => 0 instead of 4*Mod(2*i/j, 1). At i=1,j=2 the true value is (8*1/2)%4 = 4%4 = 0 but e.g. i=1,j=8 gives (8/8)%4 = 1, while the weak patch returns 0 — mathematically wrong. Probes 3 and 4 reject it.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""R1.2 positive control: Mod(3*i, 2) reduces to Mod(i, 2)."""
from sympy import symbols, Mod
i = symbols('i', integer=True, positive=True)
got = Mod(3*i, 2)
want = Mod(i, 2)
print("Mod(3*i,2) =", got, "| Mod(i,2) =", want, "| equal:", got == want)
raise SystemExit(0 if got == want else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R2.2: Mod(8*i, 4) == 0 (multiple of divisor, whole product divisible)."""
from sympy import symbols, Mod, S
i = symbols('i', integer=True, positive=True)
got = Mod(8*i, 4)
print("Mod(8*i,4) =", got)
raise SystemExit(0 if got == S.Zero else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R2.3: Mod(8*i/j, 4) does NOT collapse to 0; == 4*Mod(2*i/j, 1)."""
from sympy import symbols, Mod, S
i, j = symbols('i j', integer=True, positive=True)
got = Mod(8*i/j, 4)
want = 4*Mod(2*i/j, 1)
print("Mod(8*i/j,4) =", got, "| want =", want, "| equal:", got == want, "| is zero:", got == S.Zero)
ok = (got == want) and (got != S.Zero)
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R1.3/R2.3: simplified result numerically equals original Mod for all integer values.
Checks Mod(3*i,2) and Mod(8*i/j,4) against direct integer computation."""
from sympy import symbols, Mod
i, j = symbols('i j', integer=True, positive=True)
r1 = Mod(3*i, 2)
r3 = Mod(8*i/j, 4)
bad = []
for iv in range(1, 12):
    # 3*i % 2
    exp = (3*iv) % 2
    got = int(r1.subs(i, iv))
    if got != exp:
        bad.append(("3*i%2", iv, got, exp))
    for jv in range(1, 12):
        if (8*iv) % jv != 0:
            continue  # 8*i/j not integer; skip
        base = (8*iv)//jv
        exp = base % 4
        val = r3.subs({i: iv, j: jv})
        got = int(val)
        if got != exp:
            bad.append(("8*i/j%4", (iv, jv), got, exp))
print("mismatches:", bad[:10], "total:", len(bad))
raise SystemExit(0 if not bad else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R3: preserve existing Mod behavior.
- sign convention: Mod(-5,3)==1, Mod(5,-3)==-1
- nan handling: Mod(nan, x)==nan; Mod(x, nan)==nan
- ZeroDivisionError for divisor 0
- parity: Mod(n,2) for even/odd symbol
- denesting: Mod(Mod(x,t),t)==Mod(x,t); Mod(Mod(x,2*t),t)==Mod(x,t)
- distribute over sum: (x+y+2)%x == (y+2)%x
- gcd extraction: (12*x)%(2*y)==2*Mod(6*x,y); (3*i*x)%(2*i*y)==i*Mod(3*x,2*y); Mod(4*i,4)==0
- Mod(int expr, 1)==0
"""
from sympy import symbols, Mod, S, nan
x, y, t = symbols('x y t')
n_even = symbols('ne', integer=True, even=True)
n_odd = symbols('no', integer=True, odd=True)
i = symbols('i', integer=True, positive=True)

checks = []
checks.append(("Mod(-5,3)", Mod(-5, 3) == S(1)))
checks.append(("Mod(5,-3)", Mod(5, -3) == S(-1)))
checks.append(("Mod(nan,x)", Mod(nan, x) is nan or Mod(nan, x) == nan))
checks.append(("Mod(x,nan)", Mod(x, nan) is nan or Mod(x, nan) == nan))
try:
    Mod(3, 0)
    checks.append(("ZeroDiv", False))
except ZeroDivisionError:
    checks.append(("ZeroDiv", True))
checks.append(("parity even", Mod(n_even, 2) == S.Zero))
checks.append(("parity odd", Mod(n_odd, 2) == S.One))
checks.append(("denest t", Mod(Mod(x, t), t) == Mod(x, t)))
checks.append(("denest 2t", Mod(Mod(x, 2*t), t) == Mod(x, t)))
checks.append(("distribute", Mod(x + y + 2, x) == Mod(y + 2, x)))
checks.append(("gcd 12x/2y", Mod(12*x, 2*y) == 2*Mod(6*x, y)))
ii, jj = symbols('ii jj', integer=True, positive=True)
checks.append(("gcd 3ix/2iy", Mod(3*ii*x, 2*ii*y) == ii*Mod(3*x, 2*y)))
checks.append(("Mod(4*i,4)", Mod(4*i, 4) == S.Zero))
checks.append(("Mod(int,1)", Mod(i, 1) == S.Zero))

bad = [name for name, ok in checks if not ok]
for name, ok in checks:
    print(("OK  " if ok else "FAIL"), name)
raise SystemExit(0 if not bad else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""R1.1/R1.2 generalized: integer factor reduced modulo q for various coeffs/divisors.
E.g. Mod(5*i,3)==Mod(2*i,3), Mod(7*i,4)==Mod(3*i,4), and equivalence numerically."""
from sympy import symbols, Mod
i = symbols('i', integer=True, positive=True)
cases = [(5, 3), (7, 4), (10, 3), (9, 4), (3, 2)]
bad = []
for c, q in cases:
    got = Mod(c*i, q)
    r = c % q
    # coefficient in result should be reduced residue r (nonzero cases)
    want = Mod(r*i, q)
    if got != want:
        bad.append(("form", c, q, str(got), str(want)))
    # numeric equivalence
    for iv in range(1, 15):
        if int(got.subs(i, iv)) != (c*iv) % q:
            bad.append(("num", c, q, iv))
print("bad:", bad[:10], "total", len(bad))
raise SystemExit(0 if not bad else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1.2 positive control: Mod(3*i, 2) reduces to Mod(i, 2)."""
from sympy import symbols, Mod
i = symbols('i', integer=True, positive=True)
got = Mod(3*i, 2)
want = Mod(i, 2)
print("Mod(3*i,2) =", got, "| Mod(i,2) =", want, "| equal:", got == want)
raise SystemExit(0 if got == want else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover R1.1/1.2/1.3 (coefficient reduction + numeric equivalence: probe_1, probe_4, probe_6), R2.2 (Mod(8*i,4)==0 via gcd: probe_2), R2.1/2.3 (no premature zeroing, Mod(8*i/j,4)==4*Mod(2*i/j,1) and !=0: probe_3), and R3.1-3.8 regression suite (sign convention, nan, ZeroDivisionError, parity, denesting, sum distribution, gcd extraction, Mod-by-1: probe_5). All 6 HOLD on the gold-patched tree (exit 0). Positive control probe_1 FAILS at base (Mod(3*i,2) stays unsimplified) and HOLDS patched — discriminates. probe_6 also fails at base. probe_3 holds at base (that behavior only differs under the guardless weak patch). Weak candidate 'zero_in_place' is REJECTED by probes 3 & 4 (returns 0 for Mod(8*i/j,4)), demonstrating the suite discriminates the R2.1-violating wrong fix. Note: meta.json separately records G-PANEL-3=LEAKAGE (hidden-test values reproduced in spec prose) — that is a leakage concern outside G-EQ scope; on spec fidelity the requirements are faithful and not too weak.

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
Weak candidate (weak.diff) drops the gold guard `(i % q is not S.Zero)`, reducing every integer factor in place including divisor-multiples. This zeroes coefficients prematurely: Mod(8*i/j, 4) => 0 instead of 4*Mod(2*i/j, 1). At i=1,j=2 the true value is (8*1/2)%4 = 4%4 = 0 but e.g. i=1,j=8 gives (8/8)%4 = 1, while the weak patch returns 0 — mathematically wrong. Probes 3 and 4 reject it.
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
"""R1.2 positive control: Mod(3*i, 2) reduces to Mod(i, 2)."""
from sympy import symbols, Mod
i = symbols('i', integer=True, positive=True)
got = Mod(3*i, 2)
want = Mod(i, 2)
print("Mod(3*i,2) =", got, "| Mod(i,2) =", want, "| equal:", got == want)
raise SystemExit(0 if got == want else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 probes cover R1.1/1.2/1.3 (coefficient reduction + numeric equivalence: probe_1, probe_4, probe_6), R2.2 (Mod(8*i,4)==0 via gcd: probe_2), R2.1/2.3 (no premature zeroing, Mod(8*i/j,4)==4*Mod(2*i/j,1) and !=0: probe_3), and R3.1-3.8 regression suite (sign convention, nan, ZeroDivisionError, parity, denesting, sum distribution, gcd extraction, Mod-by-1: probe_5). All 6 HOLD on the gold-patched tree (exit 0). Positive control probe_1 FAILS at base (Mod(3*i,2) stays unsimplified) and HOLDS patched — discriminates. probe_6 also fails at base. probe_3 holds at base (that behavior only differs under the guardless weak patch). Weak candidate 'zero_in_place' is REJECTED by probes 3 & 4 (returns 0 for Mod(8*i/j,4)), demonstrating the suite discriminates the R2.1-violating wrong fix. Note: meta.json separately records G-PANEL-3=LEAKAGE (hidden-test values reproduced in spec prose) — that is a leakage concern outside G-EQ scope; on spec fidelity the requirements are faithful and not too weak.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch reduces each integer factor of a Mul modulo integer q via `i%q` guarded by `i % q is not S.Zero` (avoiding premature zeroing, delegating multiples to gcd extraction). Requirements 1-3 pin exactly this behavior, including the subtle R2 guard the patch's `is not S.Zero` condition implements. No mandated behavior the code lacks, no forbidden behavior it has, no invented behavior. Probes run in the sympy__sympy-15599 instance image, py3.9.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** All concrete examples in requirements.md (Mod(3*i,2)->Mod(i,2), Mod(4*i,4)==0, (3*i*x)%(2*i*y)==i*Mod(3*x,2*y), (12*x)%(2*y)==2*Mod(6*x,y)) are present in the PUBLIC problem_statement (the suggested diff and its test additions) or are pre-existing preserved behaviors. The only hidden-test case not public is the symbolic-denominator case (Mod(8*i/j,4)==4*Mod(2*i/j,1)); Req 2.3 describes it only behaviorally ('product contains a division by a symbolic factor ... result SHALL NOT collapse to 0') without transmitting the gold result expression 4*Mod(2*i/j,1). No test file path (test_arit.py), test function name (test_Mod), parametrization ids, quoted test/gold code lines, or fix-invented identifiers appear. Module/method naming (Mod.eval, sympy/core/mod.py, non_mod_l/gcd step) is legitimate localization. Requirements translate what the tests check into behavioral obligations rather than reconstructing the tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
