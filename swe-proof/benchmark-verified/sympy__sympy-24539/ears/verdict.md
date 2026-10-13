# P2 adversarial audit — sympy__sympy-24539

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
"""Positive control + Req1.1/1.2: as_expr(U,V,W) uses caller symbols, not ring symbols."""
from sympy import ring, ZZ, symbols

R, x, y, z = ring("x,y,z", ZZ)
f = 3*x**2*y - x*y*z + 7*z**3 + 1
U, V, W = symbols("u,v,w")
g = 3*U**2*V - U*V*W + 7*W**3 + 1

res = f.as_expr(U, V, W)
print("result:", res)
print("expected:", g)
fs = res.free_symbols
print("free_symbols:", fs)
ok = (res == g) and (U in fs and V in fs and W in fs)
# ring symbols must not appear
X, Y, Z = symbols("x,y,z")
ok = ok and (X not in fs and Y not in fs and Z not in fs)
print("OK" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.3: structural equivalence — coefficients and exponent-to-symbol correspondence
identical to ring-symbol version, differing only in position-for-position name substitution."""
from sympy import ring, ZZ, symbols

R, x, y, z = ring("x,y,z", ZZ)
f = 3*x**2*y - x*y*z + 7*z**3 + 1

own = f.as_expr()  # ring symbols x,y,z
U, V, W = symbols("u,v,w")
custom = f.as_expr(U, V, W)

X, Y, Z = symbols("x,y,z")
# Substitute caller symbols back to ring symbols -> should equal own
remapped = custom.subs({U: X, V: Y, W: Z}, simultaneous=True)
print("own:    ", own)
print("custom: ", custom)
print("remapped:", remapped)
ok = (remapped == own)
print("OK" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req2: no-argument form uses ring's own symbols and matches prior behavior."""
from sympy import ring, ZZ, symbols

R, x, y, z = ring("x,y,z", ZZ)
f = 3*x**2*y - x*y*z + 7*z**3 + 1
X, Y, Z = symbols("x,y,z")
expected = 3*X**2*Y - X*Y*Z + 7*Z**3 + 1

res = f.as_expr()
print("result:", res)
print("expected:", expected)
fs = res.free_symbols
ok = (res == expected) and {X, Y, Z} == fs
# also test another element and a constant
R2, a, b = ring("a,b", ZZ)
h = a*b + 5
A, B = symbols("a,b")
ok = ok and (h.as_expr() == A*B + 5)
print("OK" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req3.1: wrong number of symbols raises ValueError and returns no expression."""
from sympy import ring, ZZ, symbols

R, x, y, z = ring("x,y,z", ZZ)
f = 3*x**2*y - x*y*z + 7*z**3 + 1
X = symbols("x")

ok = True
# too few (1 for ngens=3)
try:
    r = f.as_expr(X)
    print("no error, returned:", r)
    ok = False
except ValueError as e:
    print("ValueError (1 sym):", e)

# too many (4)
A, B, C, D = symbols("a,b,c,d")
try:
    r = f.as_expr(A, B, C, D)
    print("no error, returned:", r)
    ok = False
except ValueError as e:
    print("ValueError (4 sym):", e)

print("OK" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req3.2: ValueError message reports both expected (ngens) and supplied counts."""
from sympy import ring, ZZ, symbols

R, x, y, z = ring("x,y,z", ZZ)  # ngens = 3
f = 3*x**2*y - x*y*z + 7*z**3 + 1
X = symbols("x")

ok = False
try:
    f.as_expr(X)
except ValueError as e:
    msg = str(e)
    print("message:", msg)
    # must report expected count (3) and supplied count (1)
    ok = ("3" in msg) and ("1" in msg)
print("OK" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + Req1.1/1.2: as_expr(U,V,W) uses caller symbols, not ring symbols."""
from sympy import ring, ZZ, symbols

R, x, y, z = ring("x,y,z", ZZ)
f = 3*x**2*y - x*y*z + 7*z**3 + 1
U, V, W = symbols("u,v,w")
g = 3*U**2*V - U*V*W + 7*W**3 + 1

res = f.as_expr(U, V, W)
print("result:", res)
print("expected:", g)
fs = res.free_symbols
print("free_symbols:", fs)
ok = (res == g) and (U in fs and V in fs and W in fs)
# ring symbols must not appear
X, Y, Z = symbols("x,y,z")
ok = ok and (X not in fs and Y not in fs and Z not in fs)
print("OK" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy__sympy-24539: PolyElement.as_expr(*symbols) must honor caller-supplied symbols. 5 probes cover all 7 acceptance criteria: probe_1 (Req1.1/1.2, positive control) caller symbols used and ring symbols absent; probe_2 (Req1.3) structural equivalence via position-for-position remap; probe_3 (Req2.1/2.2) no-arg falls back to ring symbols; probe_4 (Req3.1) wrong count (too few AND too many) raises ValueError with no return; probe_5 (Req3.2) message reports both expected(3) and supplied(1) counts.

Results: all 5 HOLD on gold-patched tree. Positive control (probe_1) FAILS at base (returns ring symbols x,y,z instead of u,v,w) — discriminating power confirmed. probes 2-5 also hold at base (base already had structural remap identity, no-arg fallback, and error-on-wrong-count with an 'not enough symbols' message containing 3 and 1) which is expected — only probe_1 encodes the core defect.

Candidate patch 'weak_message_only': fixes ONLY the error-message wording (naive/partial reading of Req3) while still assigning symbols = self.ring.symbols unconditionally, i.e. continues to ignore caller symbols. Runner-applied cleanly at base. Under it probe_1 is REJECTED (VIOLATED: returns x,y,z), while probes 2-5 pass. This demonstrates the suite discriminates a plausibly-wrong implementation and no probe-conforming weak fix survived. Verdict SOUND: >=5 probes hold on patched, positive control discriminates, >=1 candidate exercised and rejected.

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
"""Positive control + Req1.1/1.2: as_expr(U,V,W) uses caller symbols, not ring symbols."""
from sympy import ring, ZZ, symbols

R, x, y, z = ring("x,y,z", ZZ)
f = 3*x**2*y - x*y*z + 7*z**3 + 1
U, V, W = symbols("u,v,w")
g = 3*U**2*V - U*V*W + 7*W**3 + 1

res = f.as_expr(U, V, W)
print("result:", res)
print("expected:", g)
fs = res.free_symbols
print("free_symbols:", fs)
ok = (res == g) and (U in fs and V in fs and W in fs)
# ring symbols must not appear
X, Y, Z = symbols("x,y,z")
ok = ok and (X not in fs and Y not in fs and Z not in fs)
print("OK" if ok else "FAIL")
import sys; sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sympy__sympy-24539: PolyElement.as_expr(*symbols) must honor caller-supplied symbols. 5 probes cover all 7 acceptance criteria: probe_1 (Req1.1/1.2, positive control) caller symbols used and ring symbols absent; probe_2 (Req1.3) structural equivalence via position-for-position remap; probe_3 (Req2.1/2.2) no-arg falls back to ring symbols; probe_4 (Req3.1) wrong count (too few AND too many) raises ValueError with no return; probe_5 (Req3.2) message reports both expected(3) and supplied(1) counts.

Results: all 5 HOLD on gold-patched tree. Positive control (probe_1) FAILS at base (returns ring symbols x,y,z instead of u,v,w) — discriminating power confirmed. probes 2-5 also hold at base (base already had structural remap identity, no-arg fallback, and error-on-wrong-count with an 'not enough symbols' message containing 3 and 1) which is expected — only probe_1 encodes the core defect.

Candidate patch 'weak_message_only': fixes ONLY the error-message wording (naive/partial reading of Req3) while still assigning symbols = self.ring.symbols unconditionally, i.e. continues to ignore caller symbols. Runner-applied cleanly at base. Under it probe_1 is REJECTED (VIOLATED: returns x,y,z), while probes 2-5 pass. This demonstrates the suite discriminates a plausibly-wrong implementation and no probe-conforming weak fix survived. Verdict SOUND: >=5 probes hold on patched, positive control discriminates, >=1 candidate exercised and rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The one-line change moves the empty-check to the first branch (fall back to ring.symbols) and only raises on non-empty wrong-length; the correct-length branch now flows through to expr_from_dict(..., *symbols) using caller symbols. Requirements pin exactly this changed observable behavior across all three branches — no wrong boundary (they target as_expr's return, not the unchanged expr_from_dict/as_expr_dict helpers, which the intro explicitly excludes), no invented behavior, no forbidden real behavior. Base probe confirms divergence only in the caller-symbol branch; no-arg behavior is invariant, matching Req2.2.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements describe the fix behaviorally: honor caller symbols when count == ring.ngens, fall back to ring.symbols when none given, raise ValueError with expected/got counts otherwise. Everything traces to the public problem_statement, which already: names the method PolyElement.as_expr() and file sympy/polys/rings.py, states the bug (right count is ignored, wrong count errors), and even shows the U,V,W = symbols('u,v,w') example and the ring x,y,z / f = 3*x**2*y - x*y*z + 7*z**3 + 1 element. No hidden-test content appears: no test function name (test_PolyElement_as_expr), no test file path, no parametrization ids, no verbatim gold lines. The requirement that the error message report both expected and supplied counts describes behavior rather than quoting the gold string 'Wrong number of symbols, expected %s got %s'. Naming as_expr_dict / expr_from_dict / polyutils.py is legitimate localization. The requirement mirrors the problem_statement, not the tests.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
