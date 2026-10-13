# P2 adversarial audit — sympy__sympy-18698

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
Weak candidate (consolidates only multiplicities k>1, skips mult-1) rejected by probe_5: sqf_list((x-1)*(x-2)*(x-3)) returns 3 separate mult-1 entries instead of the single consolidated (x**3-6*x**2+11*x-6, 1) required by Req 2.1.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control / Req 1.4: sqf_list consolidates the two mult-3 factors."""
from sympy import symbols, sqf_list, expand
x = symbols('x')
expr = (x**2 + 1) * (x - 1)**2 * (x - 2)**3 * (x - 3)**3
coeff, factors = sqf_list(expr)
print("coeff:", coeff)
print("factors:", factors)
got = sorted(((expand(f), k) for f, k in factors), key=lambda t: (t[1], str(t[0])))
want = sorted(((expand(f), k) for f, k in
               [(x**2 + 1, 1), (x - 1, 2), (x**2 - 5*x + 6, 3)]),
              key=lambda t: (t[1], str(t[0])))
print("got :", got)
print("want:", want)
ok = coeff == 1 and got == want
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 1.1 + 1.3: no two pairs share a multiplicity; multiplicity SET preserved.
Check across several inputs. Also verifies product-of-consolidated equals
original per multiplicity group (correctness, not just uniqueness)."""
from sympy import symbols, sqf_list, expand, Poly
x = symbols('x')
inputs = [
    (x**2 + 1) * (x - 1)**2 * (x - 2)**3 * (x - 3)**3,
    (x - 1) * (x - 2) * (x - 3),                       # three mult-1 factors
    (x - 1)**2 * (x - 2)**2 * (x + 5)**3,              # two mult-2, one mult-3
    (x + 1)**4 * (x + 2)**4 * (x + 3)**4,              # three mult-4
]
allok = True
for expr in inputs:
    coeff, factors = sqf_list(expr)
    mults = [k for _, k in factors]
    unique = len(mults) == len(set(mults))
    # reconstruct: coeff * prod(f**k) must equal original (expanded)
    recon = coeff
    for f, k in factors:
        recon = recon * f**k
    correct = expand(recon) == expand(expr)
    print("expr:", expr)
    print("  factors:", factors, "unique_mult:", unique, "recon_ok:", correct)
    allok = allok and unique and correct
print("OK" if allok else "FAIL")
raise SystemExit(0 if allok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 1.5 + 4.1: input whose sqf decomposition has a distinct poly per
multiplicity is returned unchanged (no consolidation, no regression).
Use the dense single-poly example from the requirements."""
from sympy import symbols, sqf_list, expand
x = symbols('x')
expr = x**5 - 2*x**4 - 2*x**3 + 4*x**2 + x - 2
coeff, factors = sqf_list(expr)
print("coeff:", coeff)
print("factors:", factors)
mults = [k for _, k in factors]
unique = len(mults) == len(set(mults))
recon = coeff
for f, k in factors:
    recon = recon * f**k
correct = expand(recon) == expand(expr)
# Known sqf_list for this poly: (1, [(x-2,1),(x**2-1,2)]) i.e. multiplicities {1,2}
print("mults:", sorted(mults))
ok = unique and correct and sorted(mults) == [1, 2]
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 3.1/3.3: factor_list must NOT consolidate — distinct irreducible factors
sharing multiplicity 1 stay separate. This is the "SHALL keep" regression."""
from sympy import symbols, factor_list, expand
x = symbols('x')
# product of three distinct irreducible mult-1 factors
expr = (x - 1) * (x - 2) * (x - 3)
coeff, factors = factor_list(expr)
print("factor_list:", coeff, factors)
# There SHALL be 3 separate entries each multiplicity 1
mult1 = [(f, k) for f, k in factors if k == 1]
ok = len(factors) == 3 and all(k == 1 for _, k in factors)
# also the mult-3-collision example: factor_list keeps (x-2,3) and (x-3,3) separate
expr2 = (x**2 + 1) * (x - 1)**2 * (x - 2)**3 * (x - 3)**3
c2, f2 = factor_list(expr2)
print("factor_list2:", c2, f2)
mult3 = [(f, k) for f, k in f2 if k == 3]
ok = ok and len(mult3) == 2  # two separate mult-3 irreducibles
print("mult3 entries:", mult3)
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 2.1/2.2: consolidate multiplicity-1 factors of a symbolic product.
sqf_list on a product of distinct mult-1 symbolic factors -> a single mult-1
entry = expanded product."""
from sympy import symbols, sqf_list, expand
x = symbols('x')
expr = (x - 1) * (x - 2) * (x - 3)
coeff, factors = sqf_list(expr)
print("coeff:", coeff, "factors:", factors)
mult1 = [(f, k) for f, k in factors if k == 1]
ok = len(factors) == 1 and len(mult1) == 1
if ok:
    f, k = mult1[0]
    ok = expand(f) == expand((x - 1) * (x - 2) * (x - 3))
    print("consolidated factor expanded:", expand(f))
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 1.6 / 4.3 / 4.5: content/leading coeff preserved as first element, and
sqf (expression form) reconstructs the original polynomial from consolidated
factors. Use an input with a non-trivial numeric content."""
from sympy import symbols, sqf_list, sqf, expand
x = symbols('x')
# content 2, with a mult-3 collision
expr = 2 * (x - 1)**2 * (x - 2)**3 * (x - 3)**3
coeff, factors = sqf_list(expr)
print("coeff:", coeff, "factors:", factors)
recon = coeff
for f, k in factors:
    recon = recon * f**k
recon_ok = expand(recon) == expand(expr)
# sqf expression form must expand back to original
s = sqf(expr)
sqf_ok = expand(s) == expand(expr)
print("recon_ok:", recon_ok, "sqf_ok:", sqf_ok, "sqf:", s)
# multiplicities unique
mults = [k for _, k in factors]
unique = len(mults) == len(set(mults))
ok = recon_ok and sqf_ok and unique and coeff == 2
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req 1.4: sqf_list consolidates the two mult-3 factors."""
from sympy import symbols, sqf_list, expand
x = symbols('x')
expr = (x**2 + 1) * (x - 1)**2 * (x - 2)**3 * (x - 3)**3
coeff, factors = sqf_list(expr)
print("coeff:", coeff)
print("factors:", factors)
got = sorted(((expand(f), k) for f, k in factors), key=lambda t: (t[1], str(t[0])))
want = sorted(((expand(f), k) for f, k in
               [(x**2 + 1, 1), (x - 1, 2), (x**2 - 5*x + 6, 3)]),
              key=lambda t: (t[1], str(t[0])))
print("got :", got)
print("want:", want)
ok = coeff == 1 and got == want
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes cover: Req1.4 exact example (probe_1, positive control), Req1.1/1.3 uniqueness+multiplicity-set preservation+reconstruction across 4 inputs (probe_2), Req1.5/4.1 no-consolidation-needed dense poly (probe_3), Req3.1/3.3 factor_list must NOT consolidate incl. shared mult-3 (probe_4), Req2.1/2.2 mult-1 consolidation (probe_5), Req1.6/4.3/4.5 content preserved + sqf expression reconstruction (probe_6). All 6 HOLD on gold-patched tree. Positive control probe_1 FAILS at base (returns two mult-3 entries), and probes 2/5/6 also fail at base — confirmed discriminating power. Candidate patch (weak.diff) applies at base_commit, satisfies Req1/Req3/Req4-style probes (probe_1,4 HOLD) but is REJECTED by probe_5 and probe_2 because it omits mult-1 consolidation; demonstrates the suite discriminates a partial/wrong fix. No probe-conforming alternative found that would pass all probes yet fail the fix, so no TOO-WEAK finding.

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
Weak candidate (consolidates only multiplicities k>1, skips mult-1) rejected by probe_5: sqf_list((x-1)*(x-2)*(x-3)) returns 3 separate mult-1 entries instead of the single consolidated (x**3-6*x**2+11*x-6, 1) required by Req 2.1.
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
"""Positive control / Req 1.4: sqf_list consolidates the two mult-3 factors."""
from sympy import symbols, sqf_list, expand
x = symbols('x')
expr = (x**2 + 1) * (x - 1)**2 * (x - 2)**3 * (x - 3)**3
coeff, factors = sqf_list(expr)
print("coeff:", coeff)
print("factors:", factors)
got = sorted(((expand(f), k) for f, k in factors), key=lambda t: (t[1], str(t[0])))
want = sorted(((expand(f), k) for f, k in
               [(x**2 + 1, 1), (x - 1, 2), (x**2 - 5*x + 6, 3)]),
              key=lambda t: (t[1], str(t[0])))
print("got :", got)
print("want:", want)
ok = coeff == 1 and got == want
print("OK" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes cover: Req1.4 exact example (probe_1, positive control), Req1.1/1.3 uniqueness+multiplicity-set preservation+reconstruction across 4 inputs (probe_2), Req1.5/4.1 no-consolidation-needed dense poly (probe_3), Req3.1/3.3 factor_list must NOT consolidate incl. shared mult-3 (probe_4), Req2.1/2.2 mult-1 consolidation (probe_5), Req1.6/4.3/4.5 content preserved + sqf expression reconstruction (probe_6). All 6 HOLD on gold-patched tree. Positive control probe_1 FAILS at base (returns two mult-3 entries), and probes 2/5/6 also fail at base — confirmed discriminating power. Candidate patch (weak.diff) applies at base_commit, satisfies Req1/Req3/Req4-style probes (probe_1,4 HOLD) but is REJECTED by probe_5 and probe_2 because it omits mult-1 consolidation; demonstrates the suite discriminates a partial/wrong fix. No probe-conforming alternative found that would pass all probes yet fail the fix, so no TOO-WEAK finding.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The patch adds `if method == 'sqf': factors = [(reduce(mul, ...), k) for k in set(multiplicities)]`, consolidating factors by multiplicity ONLY for the sqf method. The requirements pin exactly this changed observable behavior at the correct boundary: R1/R2 mandate consolidation for sqf_list, R3 explicitly excludes factor_list/factor (enforced by the `method == 'sqf'` guard), R4 preserves everything else. Boundary is not too narrow — it captures the full behavioral change, not just one branch. Also note the patch removed the arg.is_Mul flattening branch; R2's expanded-product criterion covers the resulting mult-1 consolidation, which probes confirm. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to legitimately-named internal helpers (_symbolic_factor_list, _generic_factor_list, sqf_list/sqf, factor_list/factor) — all pre-existing public/internal API, not fix-invented identifiers (gold's new imports reduce/mul are absent from the doc). Req 1.4's expected tuple (1, [(x**2+1,1),(x-1,2),(x**2-5*x+6,3)]) is fully reconstructible from the PUBLIC problem_statement, which already gives the exact input, the buggy 4-entry output, and names x**2-5*x+6 as the correct consolidated mult-3 factor; it is not derived from hidden test_issue_8695. Req 1.5 reuses the second public example x**5-2*x**4-2*x**3+4*x**2+x-2. Reqs 2 and 3 describe the logical consequence of the public 'one factor per multiplicity' rule at multiplicity 1 and the method-conditioned scope of the fix (sqf-only, factor_list unchanged) — behavioral translation of the gold's 'if method==sqf' branch, not the tests. The hidden test_factor_terms uses sqf_list(x*(x+y))==(1,[(x**2+x*y,1)]); the doc never quotes that example, the literal x**2+x*y, any test name (test_factor_terms/test_issue_8695), file path, or parametrization id. No test-shaped case enumeration mirroring the parametrization. Behavior is described, tests are not transmitted.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
