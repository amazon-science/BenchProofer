# P2 adversarial audit — sympy__sympy-21847

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
# R1.2 (positive control): commutative, max=min=3, 3 vars -> mixed monomials of total deg 3 included
import sys
from sympy import symbols
from sympy.polys.monomials import itermonomials

x1, x2, x3 = symbols('x1 x2 x3')
got = set(itermonomials([x1, x2, x3], 3, 3))
# genuinely-degree-3 mixed monomial
mixed = x1 * x2**2
pure = {x1**3, x2**3, x3**3}
print("count:", len(got))
print("has mixed x1*x2**2:", mixed in got)
print("has all pures:", pure <= got)
# every element must have total degree exactly 3
def tot(m):
    return sum(int(m.as_poly(x1, x2, x3).degree_list()[i]) for i in range(3)) if m != 1 else 0
ok = (mixed in got) and (pure <= got)
# check no element of total degree != 3
from sympy import Poly
bad = []
for m in got:
    d = sum(Poly(m, x1, x2, x3).degree_list())
    if d != 3:
        bad.append((m, d))
print("elements not degree 3:", bad)
ok = ok and not bad
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# R1.1 & R1.3: commutative, exhaustive check total-degree window equals expected set
import sys
from sympy import symbols, Poly
from sympy.polys.monomials import itermonomials
from itertools import combinations_with_replacement

def expected(vars_, mn, mx):
    exp = set()
    n = len(vars_)
    # enumerate all exponent tuples with total degree in [mn,mx]
    from sympy import Mul
    from itertools import product as iproduct
    for degs in iproduct(range(mx+1), repeat=n):
        if mn <= sum(degs) <= mx:
            m = Mul(*[v**d for v, d in zip(vars_, degs)])
            exp.add(m)
    return exp

x, y = symbols('x y')
vars_ = [x, y]
ok = True
for mn, mx in [(3,3),(2,4),(1,3)]:
    got = set(itermonomials(vars_, mx, mn))
    exp = expected(vars_, mn, mx)
    match = got == exp
    print(f"min={mn} max={mx}: got={len(got)} exp={len(exp)} match={match}")
    if not match:
        print("  missing:", exp - got)
        print("  extra:", got - exp)
    ok = ok and match
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# R1.4: no candidate of total degree < min_degrees is yielded
import sys
from sympy import symbols, Poly
from sympy.polys.monomials import itermonomials

x, y, z = symbols('x y z')
got = set(itermonomials([x, y, z], 4, 2))
bad = []
for m in got:
    d = 0 if m == 1 else sum(Poly(m, x, y, z).degree_list())
    if d < 2:
        bad.append((m, d))
print("count:", len(got))
print("below-min elements:", bad)
sys.exit(0 if not bad else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# R2: non-commutative total-degree selection; order-distinct products yielded
import sys
from sympy import symbols
from sympy.polys.monomials import itermonomials

a, b = symbols('a b', commutative=False)
got = set(itermonomials([a, b], 2, 2))
# expected: all ordered products of total degree exactly 2
exp = {a*a, b*b, a*b, b*a}
print("count:", len(got))
print("got:", sorted(map(str, got)))
match = got == exp
print("match:", match)
if not match:
    print("missing:", exp - got, "extra:", got - exp)
sys.exit(0 if match else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# R3: regression preservation - default min (constant 1 included), min=1 excludes 1,
# min>max yields nothing, max=0 yields only 1, list mode unchanged, dedup
import sys
from sympy import symbols, Poly
from sympy.polys.monomials import itermonomials

x, y = symbols('x y')
ok = True

# R3.1 default min -> includes constant 1 and all up to max
g = list(itermonomials([x, y], 2))
print("default max=2 count:", len(g), "has 1:", (1 in set(g)))
ok = ok and (1 in set(g)) and len(g) == len(set(g))

# R3.2 min=1 excludes 1
g2 = set(itermonomials([x, y], 3, 1))
print("min=1 has 1:", (1 in g2))
ok = ok and (1 not in g2)

# R3.3 min>max -> nothing
g3 = list(itermonomials([x, y], 2, 5))
print("min>max count:", len(g3))
ok = ok and g3 == []

# R3.4 max=0 -> only 1
g4 = list(itermonomials([x, y], 0))
print("max=0:", g4)
ok = ok and set(g4) == {1}
# empty variables -> only 1
g4b = list(itermonomials([], 3))
print("empty vars:", g4b)
ok = ok and set(g4b) == {1}

# R3.5 list mode unchanged
g5 = set(itermonomials([x, y], [2, 4], [1, 2]))
exp5 = set()
from sympy import Mul
for i in range(1, 3):
    for j in range(2, 5):
        exp5.add(Mul(x**i, y**j))
print("list-mode match:", g5 == exp5)
ok = ok and g5 == exp5

# R1.5 dedup: no duplicates in output
gc = list(itermonomials([x, y], 3, 3))
print("dedup ok:", len(gc) == len(set(gc)))
ok = ok and len(gc) == len(set(gc))

sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# R4: input validation preserved
import sys
from sympy import symbols
from sympy.polys.monomials import itermonomials

x, y = symbols('x y')
ok = True

def raises(fn):
    try:
        list(fn())
        return False
    except ValueError:
        return True

# R4.1 negative int max
r1 = raises(lambda: itermonomials([x, y], -1))
# R4.2 negative int min
r2 = raises(lambda: itermonomials([x, y], 3, -1))
# R4.3 list max wrong length
r3 = raises(lambda: itermonomials([x, y], [1, 2, 3]))
# R4.4 list max, min not a list
r4 = raises(lambda: itermonomials([x, y], [1, 2], 1))
# R4.4b list min with negative entry
r5 = raises(lambda: itermonomials([x, y], [1, 2], [-1, 0]))
print("neg max:", r1, "neg min:", r2, "len mismatch:", r3, "min not list:", r4, "neg list min:", r5)
ok = all([r1, r2, r3, r4, r5])
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# R1.2 (positive control): commutative, max=min=3, 3 vars -> mixed monomials of total deg 3 included
import sys
from sympy import symbols
from sympy.polys.monomials import itermonomials

x1, x2, x3 = symbols('x1 x2 x3')
got = set(itermonomials([x1, x2, x3], 3, 3))
# genuinely-degree-3 mixed monomial
mixed = x1 * x2**2
pure = {x1**3, x2**3, x3**3}
print("count:", len(got))
print("has mixed x1*x2**2:", mixed in got)
print("has all pures:", pure <= got)
# every element must have total degree exactly 3
def tot(m):
    return sum(int(m.as_poly(x1, x2, x3).degree_list()[i]) for i in range(3)) if m != 1 else 0
ok = (mixed in got) and (pure <= got)
# check no element of total degree != 3
from sympy import Poly
bad = []
for m in got:
    d = sum(Poly(m, x1, x2, x3).degree_list())
    if d != 3:
        bad.append((m, d))
print("elements not degree 3:", bad)
ok = ok and not bad
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix under audit: change lower-bound test from `max(powers.values()) >= min_degree` to `sum(powers.values()) >= min_degree` in both the commutative and non-commutative total-degree branches of itermonomials (sympy/polys/monomials.py).

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.2, POSITIVE CONTROL): commutative, max=min=3, 3 vars -> mixed monomial x1*x2**2 present, all pures present, every element total-degree 3. PATCHED: exit0 (count 10). BASE: exit1 (count 3, mixed missing). DISCRIMINATES.
- probe_2 (R1.1/R1.3): commutative exhaustive set equality vs expected total-degree window for (3,3),(2,4),(1,3). PATCHED exit0. BASE exit1 (missing x**2*y,x*y**2,x*y).
- probe_3 (R1.4): no yielded monomial has total degree < min_degrees (3 vars, min=2). PATCHED exit0.
- probe_4 (R2, also positive control): non-commutative max=min=2 yields exactly {a**2,b**2,a*b,b*a}. PATCHED exit0. BASE exit1 (a*b,b*a missing).
- probe_5 (R3.1-3.5 & R1.5): default-min includes 1; min=1 excludes 1; min>max empty; max=0/empty-vars -> {1}; list-mode unchanged; dedup. PATCHED exit0.
- probe_6 (R4.1-4.4): validation ValueErrors preserved. PATCHED exit0.

Candidate wrong patch: weak.diff fixes ONLY the commutative branch (leaves non-commutative branch with `max(...)`). REJECTED by probe_4 (exit1: a*b,b*a missing), while probe_1/probe_6 still pass under it -> suite discriminates this too-weak/partial reading. No requirement-conforming alternative that fails hidden tests was found; the two branches are symmetric and both are pinned by the probe suite.

Conclusion: >=5 distinct probes cover R1-R4 including regression 'SHALL keep' criteria; all hold on patched; positive control fails at base; a plausible partial fix is rejected. SOUND.

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
# R1.2 (positive control): commutative, max=min=3, 3 vars -> mixed monomials of total deg 3 included
import sys
from sympy import symbols
from sympy.polys.monomials import itermonomials

x1, x2, x3 = symbols('x1 x2 x3')
got = set(itermonomials([x1, x2, x3], 3, 3))
# genuinely-degree-3 mixed monomial
mixed = x1 * x2**2
pure = {x1**3, x2**3, x3**3}
print("count:", len(got))
print("has mixed x1*x2**2:", mixed in got)
print("has all pures:", pure <= got)
# every element must have total degree exactly 3
def tot(m):
    return sum(int(m.as_poly(x1, x2, x3).degree_list()[i]) for i in range(3)) if m != 1 else 0
ok = (mixed in got) and (pure <= got)
# check no element of total degree != 3
from sympy import Poly
bad = []
for m in got:
    d = sum(Poly(m, x1, x2, x3).degree_list())
    if d != 3:
        bad.append((m, d))
print("elements not degree 3:", bad)
ok = ok and not bad
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Fix under audit: change lower-bound test from `max(powers.values()) >= min_degree` to `sum(powers.values()) >= min_degree` in both the commutative and non-commutative total-degree branches of itermonomials (sympy/polys/monomials.py).

Probes (all HOLD on gold-patched tree):
- probe_1 (R1.2, POSITIVE CONTROL): commutative, max=min=3, 3 vars -> mixed monomial x1*x2**2 present, all pures present, every element total-degree 3. PATCHED: exit0 (count 10). BASE: exit1 (count 3, mixed missing). DISCRIMINATES.
- probe_2 (R1.1/R1.3): commutative exhaustive set equality vs expected total-degree window for (3,3),(2,4),(1,3). PATCHED exit0. BASE exit1 (missing x**2*y,x*y**2,x*y).
- probe_3 (R1.4): no yielded monomial has total degree < min_degrees (3 vars, min=2). PATCHED exit0.
- probe_4 (R2, also positive control): non-commutative max=min=2 yields exactly {a**2,b**2,a*b,b*a}. PATCHED exit0. BASE exit1 (a*b,b*a missing).
- probe_5 (R3.1-3.5 & R1.5): default-min includes 1; min=1 excludes 1; min>max empty; max=0/empty-vars -> {1}; list-mode unchanged; dedup. PATCHED exit0.
- probe_6 (R4.1-4.4): validation ValueErrors preserved. PATCHED exit0.

Candidate wrong patch: weak.diff fixes ONLY the commutative branch (leaves non-commutative branch with `max(...)`). REJECTED by probe_4 (exit1: a*b,b*a missing), while probe_1/probe_6 still pass under it -> suite discriminates this too-weak/partial reading. No requirement-conforming alternative that fails hidden tests was found; the two branches are symmetric and both are pinned by the probe suite.

Conclusion: >=5 distinct probes cover R1-R4 including regression 'SHALL keep' criteria; all hold on patched; positive control fails at base; a plausible partial fix is rejected. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed gold-patched image. Confirmed: itermonomials([x1,x2],3,3)={x1**3, x1**2*x2, x1*x2**2, x2**3} (R1.2 mixed monomials now included); 3-var case includes x1*x2**2 (issue example). R2 non-comm: itermonomials([a,b],2,2)={a**2,a*b,b*a,b**2} (order-distinct products yielded). R3.1 min unspecified includes 1; R3.2 min=1 excludes 1; R3.3 min>max -> []; R3.4 max=0 -> [1]; R3.5 list mode per-variable filtering intact. R4: negative int max/min raise ValueError, list length mismatch, min-not-list-when-max-list, and negative entry in min list all raise ValueError. All 4 requirements and 19 acceptance criteria consistent with the change; boundary is the changed behavior (total-degree lower bound), not a narrow slice.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document describes the fix behaviorally and stays within what the public problem_statement already establishes. Problem_statement publicly gives: the itermonomials signature, the total-degree contract (min_degree <= total_degree(monom) <= max_degree), the max=min=3 three-variable example, and that mixed monomials like x1*x2**2 are wrongly dropped. Requirements localize the change to sympy/polys/monomials.py::itermonomials (legitimate localization) and translate the checked behavior into EARS criteria.

Checked for semantic leaks of the HIDDEN material:
- Gold patch is a one-token swap max(powers.values())>=min_degree -> sum(powers.values())>=min_degree in both comm/non-comm branches. It invents NO identifier; 'total degree = sum of exponents' is the public documented contract, not a fix-invented name. No leak.
- Hidden tests enumerate specific gold sets: {x**3, x**2*y, x*y**2, y**3} for [x,y],3,3; a large [x,y],3,2 set; and sprawling non-commutative sets for [i,j,k],2,2 and 3,2. The requirements do NOT reproduce these sets. Req 1.2 only says the result 'SHALL contain the mixed monomials of total degree 3 in addition to the pure cubes' (behavioral, no enumeration) using a two-variable analog that is the natural minimal case of the public three-variable example. Non-commutative coverage (Req 2) is described purely behaviorally ('order-distinct products treated as distinct') with NO enumeration mirroring the test's {k*i, i**2, ...} lists.
- No test function name (test_monomials), no test file path (tests/test_monomials.py), no parametrization ids, no quoted test/gold code.
- Reqs 3-4 (list mode, degenerate cases, validation ValueErrors) describe pre-existing behavior the fix must preserve, not new hidden-test content.

The document translates tested behavior into requirements (the intended purpose) without transmitting the tests themselves.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
