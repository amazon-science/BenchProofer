# P2 adversarial audit — sympy__sympy-24443

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
"""Positive control: Req1.2 + Req3.1.
Identity assignment on DihedralGroup(3) must construct a GroupHomomorphism
without ValueError and must be an isomorphism.
"""
import sys
from sympy.combinatorics.named_groups import DihedralGroup
from sympy.combinatorics.homomorphisms import homomorphism, GroupHomomorphism

D3 = DihedralGroup(3)
try:
    T = homomorphism(D3, D3, D3.generators, D3.generators)
except ValueError as e:
    print("FAIL: raised ValueError:", e)
    sys.exit(1)

print("constructed:", type(T).__name__)
if not isinstance(T, GroupHomomorphism):
    print("FAIL: not a GroupHomomorphism")
    sys.exit(1)
iso = T.is_isomorphism()
print("is_isomorphism:", iso)
sys.exit(0 if iso else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.4 + Req1.3: an invalid generator map (does not respect relations)
must raise ValueError with check=True.
D3 generators: rotation r (order 3), reflection s (order 2).
Map r -> s (order 2). Then relation r**3 == 1 maps to s**3 == s != identity,
so this map does NOT respect the defining relations and must be rejected.
"""
import sys
from sympy.combinatorics.named_groups import DihedralGroup
from sympy.combinatorics.homomorphisms import homomorphism

D3 = DihedralGroup(3)
gens = D3.generators
r, s = gens[0], gens[1]
print("r order", r.order(), "s order", s.order())
# r -> s (breaks r**3 == 1), s -> identity
images = [s, D3.identity]
try:
    T = homomorphism(D3, D3, gens, images)
    print("FAIL: expected ValueError, got", type(T).__name__)
    sys.exit(1)
except ValueError as e:
    print("raised ValueError as required:", e)
    sys.exit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req3.2: applying the constructed homomorphism to a domain generator returns
the assigned codomain image."""
import sys
from sympy.combinatorics.named_groups import DihedralGroup
from sympy.combinatorics.homomorphisms import homomorphism

D3 = DihedralGroup(3)
gens = D3.generators
T = homomorphism(D3, D3, gens, gens)
ok = True
for g, img in zip(gens, gens):
    val = T(g)
    print("T(", g, ") =", val, " expected", img)
    if val != img:
        ok = False
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req4.2: free-group / fp-group homomorphism behavior preserved.
Classic finite case: FpGroup (a^3,b^3,(ab)^2) ~ A4, mapped to AlternatingGroup(4).
Must construct and correctly report isomorphism/injective/surjective."""
import sys
from sympy.combinatorics import Permutation
from sympy.combinatorics.free_groups import free_group
from sympy.combinatorics.fp_groups import FpGroup
from sympy.combinatorics.named_groups import AlternatingGroup
from sympy.combinatorics.homomorphisms import homomorphism

ok = True
F, a, b = free_group("a, b")
G = FpGroup(F, [a**3, b**3, (a*b)**2])
c = Permutation(3)(0, 1, 2)
d = Permutation(3)(1, 2, 3)
A = AlternatingGroup(4)
T = homomorphism(G, A, [a, b], [c, d])
print("T(a*b**2*a**-1) =", T(a*b**2*a**-1), " expected", c*d**2*c**-1)
if T(a*b**2*a**-1) != c*d**2*c**-1:
    ok = False
print("is_isomorphism:", T.is_isomorphism())
if not T.is_isomorphism():
    ok = False
print("is_injective:", T.is_injective(), "is_surjective:", T.is_surjective())
if not (T.is_injective() and T.is_surjective()):
    ok = False

# trivial hom: G -> A4 by generators of G (maps into presentation of G itself)
T2 = homomorphism(G, AlternatingGroup(4), G.generators)
print("trivial hom is_trivial:", T2.is_trivial())
if not T2.is_trivial():
    ok = False

sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req4.4: argument validation preserved.
- image count mismatch -> ValueError
- generators not a subset of domain generators -> ValueError
"""
import sys
from sympy.combinatorics.named_groups import DihedralGroup
from sympy.combinatorics.homomorphisms import homomorphism

D3 = DihedralGroup(3)
gens = D3.generators
ok = True

# image count mismatch
try:
    homomorphism(D3, D3, gens, [gens[0]])
    print("FAIL: count mismatch did not raise")
    ok = False
except ValueError as e:
    print("count mismatch raised:", e)

# gens not subset of domain generators: use an element of another group
D4 = DihedralGroup(4)
try:
    homomorphism(D3, D3, [D4.generators[0]], [gens[0]])
    print("FAIL: bad gens did not raise")
    ok = False
except ValueError as e:
    print("bad gens raised:", e)

sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req4.5: with check=False, homomorphism constructs and returns without
performing relation verification (even an invalid map is accepted)."""
import sys
from sympy.combinatorics.named_groups import DihedralGroup
from sympy.combinatorics.homomorphisms import homomorphism, GroupHomomorphism

D3 = DihedralGroup(3)
gens = D3.generators
identity = D3.identity
# invalid map (would fail check) but check=False must skip verification
images = [identity, gens[1]]
try:
    T = homomorphism(D3, D3, gens, images, check=False)
except ValueError as e:
    print("FAIL: raised despite check=False:", e)
    sys.exit(1)
print("constructed with check=False:", type(T).__name__)
sys.exit(0 if isinstance(T, GroupHomomorphism) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control: Req1.2 + Req3.1.
Identity assignment on DihedralGroup(3) must construct a GroupHomomorphism
without ValueError and must be an isomorphism.
"""
import sys
from sympy.combinatorics.named_groups import DihedralGroup
from sympy.combinatorics.homomorphisms import homomorphism, GroupHomomorphism

D3 = DihedralGroup(3)
try:
    T = homomorphism(D3, D3, D3.generators, D3.generators)
except ValueError as e:
    print("FAIL: raised ValueError:", e)
    sys.exit(1)

print("constructed:", type(T).__name__)
if not isinstance(T, GroupHomomorphism):
    print("FAIL: not a GroupHomomorphism")
    sys.exit(1)
iso = T.is_isomorphism()
print("is_isomorphism:", iso)
sys.exit(0 if iso else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes _check_homomorphism._image for PermutationGroup domains (inverted generators in relator words). Six probes, all HOLD on gold-patched tree:
- probe_1 (Req1.2/Req3.1, POSITIVE CONTROL): homomorphism(D3,D3,gens,gens) constructs a GroupHomomorphism and is_isomorphism()==True. HOLDS patched, FAILS at base -> discriminates.
- probe_2 (Req1.3/Req1.4): invalid map r->s (breaks r**3==1) must raise ValueError. HOLDS patched.
- probe_3 (Req3.2): T(g) returns the assigned image for each domain generator. HOLDS patched.
- probe_4 (Req4.2): FpGroup(a^3,b^3,(ab)^2)->A4 finite hom; T on words correct, is_isomorphism/injective/surjective correct, trivial hom is_trivial. HOLDS patched.
- probe_5 (Req4.4): image-count mismatch and gens-not-subset both raise ValueError. HOLDS patched.
- probe_6 (Req4.5): check=False constructs an invalid map without verification. HOLDS patched.

Candidate wrong-fix weak.diff (naive: _image always returns codomain identity) applies at base_commit, satisfies probe_1/3/4/5/6 (identity case resolves, validation untouched, check=False untouched) but is REJECTED by probe_2 (accepts the invalid r->s map that should raise) -> suite discriminates the lazy fix. This alternative would also fail the hidden test_homomorphism (asserts a genuine relation check). Requirements are faithful and discriminating; no violation found.

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
"""Positive control: Req1.2 + Req3.1.
Identity assignment on DihedralGroup(3) must construct a GroupHomomorphism
without ValueError and must be an isomorphism.
"""
import sys
from sympy.combinatorics.named_groups import DihedralGroup
from sympy.combinatorics.homomorphisms import homomorphism, GroupHomomorphism

D3 = DihedralGroup(3)
try:
    T = homomorphism(D3, D3, D3.generators, D3.generators)
except ValueError as e:
    print("FAIL: raised ValueError:", e)
    sys.exit(1)

print("constructed:", type(T).__name__)
if not isinstance(T, GroupHomomorphism):
    print("FAIL: not a GroupHomomorphism")
    sys.exit(1)
iso = T.is_isomorphism()
print("is_isomorphism:", iso)
sys.exit(0 if iso else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance fixes _check_homomorphism._image for PermutationGroup domains (inverted generators in relator words). Six probes, all HOLD on gold-patched tree:
- probe_1 (Req1.2/Req3.1, POSITIVE CONTROL): homomorphism(D3,D3,gens,gens) constructs a GroupHomomorphism and is_isomorphism()==True. HOLDS patched, FAILS at base -> discriminates.
- probe_2 (Req1.3/Req1.4): invalid map r->s (breaks r**3==1) must raise ValueError. HOLDS patched.
- probe_3 (Req3.2): T(g) returns the assigned image for each domain generator. HOLDS patched.
- probe_4 (Req4.2): FpGroup(a^3,b^3,(ab)^2)->A4 finite hom; T on words correct, is_isomorphism/injective/surjective correct, trivial hom is_trivial. HOLDS patched.
- probe_5 (Req4.4): image-count mismatch and gens-not-subset both raise ValueError. HOLDS patched.
- probe_6 (Req4.5): check=False constructs an invalid map without verification. HOLDS patched.

Candidate wrong-fix weak.diff (naive: _image always returns codomain identity) applies at base_commit, satisfies probe_1/3/4/5/6 (identity case resolves, validation untouched, check=False untouched) but is REJECTED by probe_2 (accepts the invalid r->s map that should raise) -> suite discriminates the lazy fix. This alternative would also fail the hidden test_homomorphism (asserts a genuine relation check). Requirements are faithful and discriminating; no violation found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The changed observable behavior is _check_homomorphism correctly evaluating relator words (incl. inverted generators) for PermutationGroup domains. Requirements pin this at the homomorphism()/_check_homomorphism boundary rather than a narrow branch, and preserve fp/free-group semantics. Probes run on gold-patched instance image (exit 0) and base (R1.2 VIOLATED, confirming the twin discriminator).


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement already contains the DihedralGroup(3) reproduction (exact homomorphism(D3,D3,D3.generators,D3.generators) call), the ValueError text, the root-cause diagnosis (_image, `r[i] in gens` failing on inverted generators), and the target file homomorphisms.py. The requirements localize the change to homomorphism/_check_homomorphism (legitimate) and translate behavior into EARS criteria. The only detail not in the problem_statement is Req 3.1's `is_isomorphism()` outcome, which mirrors the hidden test's `assert T.is_isomorphism()` — but this is a behavioral description of the intended result using a public API method, not quoted test code, a test path/name/id, or a parametrization enumeration. No gold-invented identifiers (symbols_to_domain_generators, ext_rep) or verbatim gold/test lines are leaked; array_form/(symbol,power) are public presentation concepts. Behavioral translation, not test transmission.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
