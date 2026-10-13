# P2 adversarial audit — sympy__sympy-13551

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
'''Req1.2 / positive control: product of n + 1/2**k over k=0..n-1, subs n=2 == 15/2.'''
from sympy import Product, Symbol, Rational, S
k = Symbol('k')
n = Symbol('n')
p = Product(n + 1/2**k, (k, 0, n - 1)).doit()
val = p.subs(n, 2).doit()
val = S(val)
print("evaluated:", p)
print("subs n=2:", val, "expected 15/2 =", Rational(15, 2))
import sys
sys.exit(0 if val == Rational(15, 2) else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
'''Req1.1/1.3/1.4: genuine product for additive term equals product of factors.
Check n + 1/2**k over k=0..2 (n=3 positions) matches direct multiplication for several n.'''
from sympy import Product, Symbol, S
k = Symbol('k')
n = Symbol('n')
p = Product(n + 1/2**k, (k, 0, n - 1)).doit()
print("closed form:", p)
ok = True
for N in (2, 3, 4):
    got = S(p.subs(n, N).doit())
    direct = S(1)
    for kk in range(0, N):
        direct *= (N + S(1)/2**kk)
    direct = S(direct)
    print("N=%d got=%s direct=%s" % (N, got, direct))
    if got != direct:
        ok = False
import sys
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
'''Req1 (second demonstration): product of k**(2/3)+1 over 0..n-1 must NOT collapse to 1.
Check numeric value for n=3 equals genuine product.'''
from sympy import Product, Symbol, S, Rational
k = Symbol('k')
n = Symbol('n')
p = Product(k**Rational(2, 3) + 1, (k, 0, n - 1)).doit()
print("closed form:", p)
got = S(p.subs(n, 3).doit())
direct = S(1)
for kk in range(0, 3):
    direct *= (S(kk)**Rational(2, 3) + 1)
direct = S(direct)
# compare numerically to be safe
diff = (got - direct)
print("n=3 got=%s direct=%s simplify(diff)=%s" % (got, direct, diff.simplify()))
import sys
# must be equal and not the collapsed value 1
ok = (diff.simplify() == 0) and (got != 1)
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
'''Req2 regression: constant, definite-range, polynomial, single-position cases preserved.'''
from sympy import Product, Symbol, S, factorial, oo, Rational, simplify
k = Symbol('k')
n = Symbol('n')
a = Symbol('a')
checks = []
# Req2.1 constant term -> a**(#positions); here term independent of k over 0..n-1
c = Symbol('c')
r = Product(c, (k, 0, n - 1)).doit()
checks.append(("const", r == c**n))
# term identically 1
r1 = Product(S(1), (k, 1, n)).doit()
checks.append(("one", r1 == 1))
# Req2.3 polynomial: Product(k, (k,1,n)) == factorial(n)
rp = Product(k, (k, 1, n)).doit()
checks.append(("poly_factorial", rp == factorial(n)))
# Product(k**2,(k,1,n)) == factorial(n)**2
rp2 = Product(k**2, (k, 1, n)).doit()
checks.append(("poly_sq", simplify(rp2 - factorial(n)**2) == 0))
# Req2.2 definite range explicit product
rd = Product(k**2 + 1, (k, 1, 3)).doit()
checks.append(("definite", rd == (1**2+1)*(2**2+1)*(3**2+1)))
# Req2.6 single position
rs = Product(k + 5, (k, 3, 3)).doit()
checks.append(("single", rs == 8))
ok = True
for name, c in checks:
    print(name, c)
    if not c:
        ok = False
import sys
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
'''Req2.4 rational + Req2.5 multiplicative + Req2.3 polynomial special/rising-factorial form.'''
from sympy import Product, Symbol, S, simplify
k = Symbol('k')
n = Symbol('n')
checks = []
# Req2.4 rational function: Product(k/(k+1),(k,1,n)) == 1/(n+1)
rr = Product(k/(k + 1), (k, 1, n)).doit()
checks.append(("rational", simplify(rr - 1/(n + 1)) == 0))
# Req2.5 multiplicative factor-wise definite
rm = Product(k*(k + 1), (k, 1, 3)).doit()
checks.append(("mult_definite", rm == (1*2)*(2*3)*(3*4)))
# Req2.5 multiplicative symbolic: Product(k*(k+1),(k,1,n)) subs n=4 matches direct
rms = Product(k*(k + 1), (k, 1, n)).doit()
direct = 1
for kk in range(1, 5):
    direct *= kk*(kk + 1)
checks.append(("mult_symbolic", S(rms.subs(n, 4).doit()) == direct))
# Req2.3 polynomial closed form via gamma/factorial + correctness on subs
rp = Product(k + 3, (k, 1, n)).doit()
sp = str(rp)
checks.append(("poly_form", ('gamma' in sp or 'factorial' in sp or 'RisingFactorial' in sp)))
val = S(rp.subs(n, 3).doit())
dp = (1+3)*(2+3)*(3+3)
checks.append(("poly_value", val == dp))
ok = True
for name, c in checks:
    print(name, c)
    if not c:
        ok = False
import sys
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
'''Req3: rewrite Product to Sum yields exp(Sum(log(term))).'''
from sympy import Product, Symbol, Sum, log, exp, S
k = Symbol('k')
n = Symbol('n')
term = n + 1/2**k
P = Product(term, (k, 0, n - 1))
r = P.rewrite(Sum)
expected = exp(Sum(log(term), (k, 0, n - 1)))
print("rewrite:", r)
print("expected:", expected)
import sys
sys.exit(0 if r == expected else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
'''Req1.2 / positive control: product of n + 1/2**k over k=0..n-1, subs n=2 == 15/2.'''
from sympy import Product, Symbol, Rational, S
k = Symbol('k')
n = Symbol('n')
p = Product(n + 1/2**k, (k, 0, n - 1)).doit()
val = p.subs(n, 2).doit()
val = S(val)
print("evaluated:", p)
print("subs n=2:", val, "expected 15/2 =", Rational(15, 2))
import sys
sys.exit(0 if val == Rational(15, 2) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy-13551: additive-term branch of Product._eval_product replaced product-of-sum with sum-of-products; gold replaces it with exp(Sum(log(p))).

6 probes, all HOLD on gold-patched tree:
- probe_1 (Req1.2, POSITIVE CONTROL): Product(n+1/2**k,(k,0,n-1)).doit() subs n=2 == 15/2. HOLDS patched, FAILS at base (base gives 9/2).
- probe_2 (Req1.1/1.3/1.4): closed form equals genuine product of factors for N=2,3,4. HOLDS patched, FAILS base.
- probe_3 (Req1 second demonstration): Product(k**(2/3)+1,(k,0,n-1)) at n=3 equals genuine product and != collapsed value 1. HOLDS patched, FAILS base.
- probe_4 (Req2.1/2.2/2.3/2.6): constant->c**n, identity 1, poly factorial(n), factorial**2, definite-range explicit product, single-position. HOLDS patched.
- probe_5 (Req2.3/2.4/2.5): rational Product(k/(k+1))==1/(n+1), multiplicative factor-wise (definite + symbolic subs), polynomial rising-factorial/gamma form + value. HOLDS patched.
- probe_6 (Req3): Product.rewrite(Sum) == exp(Sum(log(term),(k,a,n))). HOLDS patched.

Note: an early probe_5 check of the convergent infinite product Product(1-1/k**2,(k,2,oo)) was a PROBE ARTIFACT — this sympy version leaves it unevaluated on BOTH base and patched (result is the unevaluated Product), so it is not a spec violation; removed it and replaced with valid regression checks.

Discrimination (candidate wrong patches, both apply at base_commit):
- weak_none (additive branch returns None / leaves unevaluated): REJECTED — probes 1 and 2 fail (no closed form => 15/2 not produced).
- weak_buggy (retains base sum-of-products behavior): REJECTED — probes 1,2,3 fail (reproduces the 9/2 bug).
Both requirements-plausible weak readings are caught, so the suite discriminates. No too-weak candidate found that passes all probes.

Verdict SOUND: >=5 distinct probes all hold on patched; positive control discriminates (holds patched, fails base); >=1 candidate exercised and >=2 rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
'''Req1.2 / positive control: product of n + 1/2**k over k=0..n-1, subs n=2 == 15/2.'''
from sympy import Product, Symbol, Rational, S
k = Symbol('k')
n = Symbol('n')
p = Product(n + 1/2**k, (k, 0, n - 1)).doit()
val = p.subs(n, 2).doit()
val = S(val)
print("evaluated:", p)
print("subs n=2:", val, "expected 15/2 =", Rational(15, 2))
import sys
sys.exit(0 if val == Rational(15, 2) else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy-13551: additive-term branch of Product._eval_product replaced product-of-sum with sum-of-products; gold replaces it with exp(Sum(log(p))).

6 probes, all HOLD on gold-patched tree:
- probe_1 (Req1.2, POSITIVE CONTROL): Product(n+1/2**k,(k,0,n-1)).doit() subs n=2 == 15/2. HOLDS patched, FAILS at base (base gives 9/2).
- probe_2 (Req1.1/1.3/1.4): closed form equals genuine product of factors for N=2,3,4. HOLDS patched, FAILS base.
- probe_3 (Req1 second demonstration): Product(k**(2/3)+1,(k,0,n-1)) at n=3 equals genuine product and != collapsed value 1. HOLDS patched, FAILS base.
- probe_4 (Req2.1/2.2/2.3/2.6): constant->c**n, identity 1, poly factorial(n), factorial**2, definite-range explicit product, single-position. HOLDS patched.
- probe_5 (Req2.3/2.4/2.5): rational Product(k/(k+1))==1/(n+1), multiplicative factor-wise (definite + symbolic subs), polynomial rising-factorial/gamma form + value. HOLDS patched.
- probe_6 (Req3): Product.rewrite(Sum) == exp(Sum(log(term),(k,a,n))). HOLDS patched.

Note: an early probe_5 check of the convergent infinite product Product(1-1/k**2,(k,2,oo)) was a PROBE ARTIFACT — this sympy version leaves it unevaluated on BOTH base and patched (result is the unevaluated Product), so it is not a spec violation; removed it and replaced with valid regression checks.

Discrimination (candidate wrong patches, both apply at base_commit):
- weak_none (additive branch returns None / leaves unevaluated): REJECTED — probes 1 and 2 fail (no closed form => 15/2 not produced).
- weak_buggy (retains base sum-of-products behavior): REJECTED — probes 1,2,3 fail (reproduces the 9/2 bug).
Both requirements-plausible weak readings are caught, so the suite discriminates. No too-weak candidate found that passes all probes.

Verdict SOUND: >=5 distinct probes all hold on patched; positive control discriminates (holds patched, fails base); >=1 candidate exercised and >=2 rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe on gold-patched tree: p = 2**(-n**2/2 + n/2)*exp(Sum(log(2**k*n+1),(k,0,n-1))); subs n=2 (with .doit()) = 15/2; second issue example k**(2/3)+1 at n=2 evaluates to 2 (true product 1*2), no longer the bogus 1. Note: requirements correctly state the closed form must be 're-evaluated' after substitution (Req 1.2/1.3 say 'after substituting n=2 and re-evaluating' / 'the result is re-evaluated') — this matches reality, since the raw .subs leaves an unevaluated Sum that needs .doit()/simplify to reach 15/2. This nuance is faithfully captured, not glossed. The patch is a one-line change confined to the additive branch of _eval_product; the modeling boundary in the requirements (the additive-with-numeric-denominator case) is exactly the changed behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Hidden test (test_issue_13546) only asserts Product(n+1/2**k,(k,0,n-1)).doit().subs(n,2).doit()==15/2. Every concrete value the requirements transmit (the n+1/2**k example, wrong 9/2, correct 15/2, the (2+2**0)*(2+2**(-1)) expansion, n=2) is already verbatim in the PUBLIC problem_statement. Module/function localization (sympy/concrete/products.py, _eval_product additive branch) is legitimate. The k**(2/3)+1 -> 1 mention mirrors a PRE-EXISTING unchanged source comment (n**(2/3)+1), not the gold edit, and matches no hidden test. Req 3's product=exp(Sum(log(term))) matches the gold's exp(Sum(log(p))) mechanism but is (i) a universal math identity and (ii) the pre-existing, publicly-documented rewrite(Sum) feature (test_rewrite_Sum is PASS_TO_PASS); it reconstructs no hidden test. No test names/paths/ids, no parametrization enumeration, no fix-invented identifiers, no verbatim gold code.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
