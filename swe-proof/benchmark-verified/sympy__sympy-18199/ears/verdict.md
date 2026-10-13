# P2 adversarial audit — sympy__sympy-18199

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
# Requirement 1.1 & 1.2: zero root reported when a % p == 0, prime p, n>2.
from sympy.ntheory.residue_ntheory import nthroot_mod

a, n, p = 17*17, 5, 17
res = nthroot_mod(a, n, p)
print("nthroot_mod(17*17, 5, 17) =", res)
# Criterion 2: returned value SHALL be [0]
ok = (res == [0])
print("equals [0]:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Requirement 2.1: composite modulus does not raise NotImplementedError, computes roots.
from sympy.ntheory.residue_ntheory import nthroot_mod

try:
    res = nthroot_mod(8, 3, 15)
    print("nthroot_mod(8,3,15) =", res)
except NotImplementedError as e:
    print("raised NotImplementedError:", e)
    raise SystemExit(1)
# must produce a result (list) not error
ok = res is not None
print("produced result (not error):", ok)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Requirement 2.3 & 2.4: composite result sorted, no duplicates, complete & correct.
# Compare against brute-force full solution set over [0, m).
from sympy.ntheory.residue_ntheory import nthroot_mod

def brute(a, n, m):
    return [x for x in range(m) if pow(x, n, m) == a % m]

cases = [(8, 3, 15), (4, 2, 15), (9, 2, 21), (0, 3, 12), (16, 4, 45)]
allok = True
for a, n, m in cases:
    res = nthroot_mod(a, n, m, all_roots=True)
    if res is None:
        res = []
    bf = brute(a, n, m)
    sorted_ok = (res == sorted(res))
    nodup = (len(res) == len(set(res)))
    complete = (sorted(set(res)) == bf)
    # each returned residue actually satisfies congruence
    valid = all(pow(int(x), n, m) == a % m for x in res)
    print(f"a={a} n={n} m={m}: res={res} brute={bf} sorted={sorted_ok} nodup={nodup} complete={complete} valid={valid}")
    allok = allok and sorted_ok and nodup and complete and valid
raise SystemExit(0 if allok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Requirement 2.5: composite modulus with no root modulo some prime-power factor
# yields empty result, not an error.
from sympy.ntheory.residue_ntheory import nthroot_mod

def brute(a, n, m):
    return [x for x in range(m) if pow(x, n, m) == a % m]

# choose a case with no solution. x**2 ≡ 3 (mod 15): check brute is empty.
a, n, m = 3, 2, 15
bf = brute(a, n, m)
print("brute roots of x^2=3 mod 15:", bf)
try:
    res = nthroot_mod(a, n, m, all_roots=True)
except Exception as e:
    print("raised:", type(e).__name__, e)
    raise SystemExit(1)
print("nthroot_mod result:", res)
# empty result: either [] or None
empty = (res is None) or (res == [])
ok = (bf == []) and empty
print("no roots and empty returned:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Requirement 3.1/3.3: preserve prime-modulus behavior for documented examples.
from sympy.ntheory.residue_ntheory import nthroot_mod

r1 = nthroot_mod(11, 4, 19, True)
r2 = nthroot_mod(68, 3, 109)
print("nthroot_mod(11,4,19,True) =", r1)
print("nthroot_mod(68,3,109) =", r2)
ok = (r1 == [8, 11]) and (r2 == 23)
print("matches documented results:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Requirement 3.2: prime p, a%p!=0, a not an n-th power residue -> None.
from sympy.ntheory.residue_ntheory import nthroot_mod, is_nthpow_residue

# find a case: p=17, n=3? gcd(3,16)=1 so all residues are nth powers. pick n dividing p-1.
# p=31, n=5, (p-1)%n==0. find a that is not a 5th power residue mod 31.
p, n = 31, 5
a = None
for cand in range(2, p):
    if cand % p != 0 and not is_nthpow_residue(cand, n, p):
        a = cand
        break
print("chosen a,n,p =", a, n, p)
res = nthroot_mod(a, n, p, all_roots=True)
print("nthroot_mod result:", res)
ok = (res is None) or (res == [])
print("returns None/empty for non-residue:", ok)
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_2.py`

```python
# Requirement 2.1: composite modulus does not raise NotImplementedError, computes roots.
from sympy.ntheory.residue_ntheory import nthroot_mod

try:
    res = nthroot_mod(8, 3, 15)
    print("nthroot_mod(8,3,15) =", res)
except NotImplementedError as e:
    print("raised NotImplementedError:", e)
    raise SystemExit(1)
# must produce a result (list) not error
ok = res is not None
print("produced result (not error):", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Six probes cover the requirements: P1 (Req1.1/1.2: nthroot_mod(17*17,5,17)==[0]), P2 (Req2.1: composite modulus no NotImplementedError), P3 (Req2.3/2.4: composite results sorted, dedup, complete & valid vs brute-force over several cases incl a=0), P4 (Req2.5: no-root composite modulus returns empty not error), P5 (Req3.1/3.3: documented prime examples [8,11] and 23 preserved), P6 (Req3.2: non-nth-power residue returns None). All 6 HOLD on the gold-patched tree.

Discriminating power: P1, P2, P3 FAIL at base (base drops the zero root and raises NotImplementedError for composite p) and HOLD patched — positive controls confirmed. P4/P5/P6 hold at base too (regression-preservation criteria).

Wrong-fix candidate 'zero_root_only_partial_fix' adds only the `a%p==0 -> [0]` prime case but leaves the composite `NotImplementedError`. Under this candidate P1/P4/P5/P6 pass but P2 and P3 REJECT it (still raises NotImplementedError for composite moduli), demonstrating the suite discriminates a plausible partial fix. No requirements-conforming alternative found that would evade the hidden tests. Verdict SOUND.

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
# Requirement 2.1: composite modulus does not raise NotImplementedError, computes roots.
from sympy.ntheory.residue_ntheory import nthroot_mod

try:
    res = nthroot_mod(8, 3, 15)
    print("nthroot_mod(8,3,15) =", res)
except NotImplementedError as e:
    print("raised NotImplementedError:", e)
    raise SystemExit(1)
# must produce a result (list) not error
ok = res is not None
print("produced result (not error):", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Six probes cover the requirements: P1 (Req1.1/1.2: nthroot_mod(17*17,5,17)==[0]), P2 (Req2.1: composite modulus no NotImplementedError), P3 (Req2.3/2.4: composite results sorted, dedup, complete & valid vs brute-force over several cases incl a=0), P4 (Req2.5: no-root composite modulus returns empty not error), P5 (Req3.1/3.3: documented prime examples [8,11] and 23 preserved), P6 (Req3.2: non-nth-power residue returns None). All 6 HOLD on the gold-patched tree.

Discriminating power: P1, P2, P3 FAIL at base (base drops the zero root and raises NotImplementedError for composite p) and HOLD patched — positive controls confirmed. P4/P5/P6 hold at base too (regression-preservation criteria).

Wrong-fix candidate 'zero_root_only_partial_fix' adds only the `a%p==0 -> [0]` prime case but leaves the composite `NotImplementedError`. Under this candidate P1/P4/P5/P6 pass but P2 and P3 REJECT it (still raises NotImplementedError for composite moduli), demonstrating the suite discriminates a plausible partial fix. No requirements-conforming alternative found that would evade the hidden tests. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Gold patch only edits sympy/ntheory/residue_ntheory.py (adds _nthroot_mod_composite, reorders so composite -> composite solver, a%p==0 -> [0], moved is_nthpow_residue None check). Req4 references solveset.py but only asserts DOWNSTREAM behavior of the already-existing delegation (no code there changed) -- probed and holds, so it is a faithful description of the observable effect, not an invention. Req1's n>2 scope is a faithful narrowing: for n==2 the function delegates to sqrt_mod before the a%p==0 branch, and Req3.4 covers that path (verified nthroot_mod(49,2,7,True)=[0]). Req1 crit2 [0] holds even for all_roots=False, matching the patch's unconditional 'return [0]'.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements translate the gold behavior into EARS requirements without transmitting the hidden tests. No verbatim/near-verbatim test values leak: none of the distinctive parametrized outputs from test_residue.py ([4,22], [3,9,15,21,27,33], (4,3,3249000)->[], (36010,8,87382)->[40208,47174], (0,7,100)->[0..90]) or test_solveset.py's Mod(x**3,8)-1->8n+1 / Mod(x**4,9)-4 cases appear. No test function/file names, paths, or invented identifiers (_nthroot_mod_composite, cartes) are named. The composite-modulus algorithm prose (factor->prime-power roots->Hensel lift->CRT recombine) describes the fix's approach, which is legitimate behavioral/localization content, not test code. Req 3's examples ([8,11] for nthroot_mod(11,4,19,True); root 23 for nthroot_mod(68,3,109)) are drawn from the function's PUBLIC docstring, not the hidden test file (which uses (43,3,109)). Req 1's example (17*17,5,17) is straight from the public problem_statement. Named symbols (nthroot_mod, _invert_modular/_solve_modular, solveset, sqrt_mod, residue_ntheory.py) are pre-existing public functions used for legitimate localization. The solveset/composite behavior goes beyond the problem_statement but is described generically (behavioral requirements), not as reconstructed test cases.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
