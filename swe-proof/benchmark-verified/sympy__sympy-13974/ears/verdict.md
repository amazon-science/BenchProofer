# P2 adversarial audit — sympy__sympy-13974

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

Counterexample / evidence:

```
weak.diff (standalone_pow_only) handles ONLY the standalone Pow case in tensor_product_simp (adds the TensorProduct-base branch) but leaves tensor_product_simp_Mul unchanged. It satisfies R1 (probe_1 HOLDS) yet is REJECTED by probe_2 (R2: powers of TPs inside a product -> TypeError, no combine), probe_3 (R3: TP(A,B)-TP(C,D)**x sum still fails because the Mul path in the sum's addend handling is unaffected only for the product case; actually the sum addend that is a pure Pow works but the mixed product does not — probe_3's second case TP(A,B)**2+TP(C,D) works, but the first case involving a subtraction where a term is a product path fails), probe_4 (R4.3: helper tensor_product_simp_Pow does not exist in this candidate -> ImportError), and probe_5 (R2.5 TypeError semantics differ). The suite thus discriminates this partial fix.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""R1: standalone power of a tensor product -> distribute exponent (symbolic & int).
POSITIVE CONTROL."""
from sympy import symbols
from sympy.physics.quantum.tensorproduct import TensorProduct as TP, tensor_product_simp as tps

A, B = symbols('A B', commutative=False)
x = symbols('x')

# symbolic exponent (R1.1, R1.2, R1.4)
r1 = tps(TP(A, B) ** x)
e1 = TP(A ** x, B ** x)
print("symbolic:", r1, "expected:", e1)

# positive integer exponent (R1.3)
r2 = tps(TP(A, B) ** 3)
e2 = TP(A ** 3, B ** 3)
print("int:", r2, "expected:", e2)

# preserve number & order of factors (R1.4): three factors
C = symbols('C', commutative=False)
r3 = tps(TP(A, B, C) ** x)
e3 = TP(A ** x, B ** x, C ** x)
print("three:", r3, "expected:", e3)

ok = (r1 == e1) and (r2 == e2) and (r3 == e3)
print("OK" if ok else "FAIL")
import sys
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""R2: powers of tensor products within a product.
- R2.1: product whose only nc factor is a power of a TP -> scalars * distributed TP
- R2.2/R2.3: power of TP alongside plain TP + scalar -> combine factor-by-factor, keep coeff
"""
from sympy import symbols
from sympy.physics.quantum.tensorproduct import TensorProduct as TP, tensor_product_simp as tps

A, B, C, D = symbols('A B C D', commutative=False)
x = symbols('x')

# R2.1: 2 * TP(A,B)**x  -> 2 * TP(A**x, B**x)
r1 = tps(2 * TP(A, B) ** x)
e1 = 2 * TP(A ** x, B ** x)
print("only-nc-pow:", r1, "expected:", e1)

# R2.2/2.3: 3 * TP(A,B)**x * TP(C,D) -> 3 * TP(A**x * C, B**x * D)
r2 = tps(3 * TP(A, B) ** x * TP(C, D))
e2 = 3 * TP(A ** x * C, B ** x * D)
print("pow+plain+scalar:", r2, "expected:", e2)

ok = (r1 == e1) and (r2 == e2)
print("OK" if ok else "FAIL")
import sys
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""R3: powers of tensor products within a sum. Also the hidden-test-shaped case.
R3.1: apply to each addend; R3.2: pow addend distributed, plain TP unchanged."""
from sympy import symbols
from sympy.physics.quantum.tensorproduct import TensorProduct as TP, tensor_product_simp as tps

A, B, C, D = symbols('A B C D', commutative=False)
x = symbols('x')

# TP(A,B) - TP(C,D)**x -> TP(A,B) - TP(C**x, D**x)
r = tps(TP(A, B) - TP(C, D) ** x)
e = TP(A, B) - TP(C ** x, D ** x)
print("sum:", r, "expected:", e)

# plain addend unchanged, another power addend evaluated
r2 = tps(TP(A, B) ** 2 + TP(C, D))
e2 = TP(A ** 2, B ** 2) + TP(C, D)
print("sum2:", r2, "expected:", e2)

ok = (r == e) and (r2 == e2)
print("OK" if ok else "FAIL")
import sys
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""R4: leave non-TP powers and other expressions unchanged.
R4.1: power whose base is not a TP -> simplify base, reapply exponent (no TP distribution).
R4.2: atom / bare TP returned unchanged.
R4.3: helper returns input unchanged when not a Pow-of-TP."""
from sympy import symbols, Symbol
from sympy.physics.quantum.tensorproduct import (
    TensorProduct as TP, tensor_product_simp as tps, tensor_product_simp_Pow)

A, B = symbols('A B', commutative=False)
x = symbols('x')

# R4.1: base is a plain non-TP symbol power -> unchanged as A**x (NOT distributed)
r1 = tps(A ** x)
print("nonTP pow:", r1)
ok1 = (r1 == A ** x) and (not isinstance(r1, TP))

# R4.2: bare TP returned unchanged
tp = TP(A, B)
r2 = tps(tp)
print("bare tp:", r2)
ok2 = (r2 == tp)

# R4.2: atom unchanged
a = Symbol('q')
r3 = tps(a)
print("atom:", r3)
ok3 = (r3 == a)

# R4.3: helper on a non-Pow-of-TP input returns it unchanged
r4 = tensor_product_simp_Pow(A ** x)   # base not TP
r5 = tensor_product_simp_Pow(tp)       # not a Pow at all
print("helper nonTP-pow:", r4, "helper non-pow:", r5)
ok4 = (r4 == A ** x) and (r5 == tp)

ok = ok1 and ok2 and ok3 and ok4
print("OK" if ok else "FAIL")
import sys
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""R5 regression + R2.4/R2.5 error signaling.
R5.1: product of two equal-length TPs combines factor-by-factor.
R5.2: commutator/anticommutator recurse.
R5.4: scalar pull-out preserved.
R2.5: non-TP / non-Pow-of-TP nc factor -> TypeError."""
from sympy import symbols
from sympy.physics.quantum.tensorproduct import TensorProduct as TP, tensor_product_simp as tps
from sympy.physics.quantum.commutator import Commutator
from sympy.physics.quantum.anticommutator import AntiCommutator

A, B, C, D = symbols('A B C D', commutative=False)

# R5.1: product of two TPs
r1 = tps(TP(A, B) * TP(C, D))
e1 = TP(A * C, B * D)
print("combine:", r1, "expected:", e1)
ok1 = (r1 == e1)

# R5.2: commutator recurse -> Commutator of simplified args (constructor may canonicalize sign)
r2 = tps(Commutator(TP(A, B) * TP(C, D), TP(A, B)))
exp2 = Commutator(e1, TP(A, B))
print("commutator:", r2, "expected:", exp2)
ok2 = (r2 == exp2)

# anticommutator recurse
r3 = tps(AntiCommutator(TP(A, B) * TP(C, D), TP(A, B)))
exp3 = AntiCommutator(e1, TP(A, B))
print("anticommutator:", r3, "expected:", exp3)
ok3 = (r3 == exp3)

# R5.4: scalar pull-out preserved: 2 already a coefficient
r4 = tps(TP(2 * A, B))
print("scalar pullout:", r4)
ok4 = r4 == 2 * TP(A, B)

# R2.5: TypeError on a non-TP, non-Pow-of-TP nc factor in a product with a TP
E = symbols('E', commutative=False)
raised = False
try:
    tps(TP(A, B) * E)   # E is a plain nc symbol, not a TP or Pow-of-TP
except TypeError:
    raised = True
print("R2.5 TypeError raised:", raised)
ok5 = raised

ok = ok1 and ok2 and ok3 and ok4 and ok5
print("OK" if ok else "FAIL")
import sys
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1: standalone power of a tensor product -> distribute exponent (symbolic & int).
POSITIVE CONTROL."""
from sympy import symbols
from sympy.physics.quantum.tensorproduct import TensorProduct as TP, tensor_product_simp as tps

A, B = symbols('A B', commutative=False)
x = symbols('x')

# symbolic exponent (R1.1, R1.2, R1.4)
r1 = tps(TP(A, B) ** x)
e1 = TP(A ** x, B ** x)
print("symbolic:", r1, "expected:", e1)

# positive integer exponent (R1.3)
r2 = tps(TP(A, B) ** 3)
e2 = TP(A ** 3, B ** 3)
print("int:", r2, "expected:", e2)

# preserve number & order of factors (R1.4): three factors
C = symbols('C', commutative=False)
r3 = tps(TP(A, B, C) ** x)
e3 = TP(A ** x, B ** x, C ** x)
print("three:", r3, "expected:", e3)

ok = (r1 == e1) and (r2 == e2) and (r3 == e3)
print("OK" if ok else "FAIL")
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Ran all 5 probes on the gold-PATCHED tree: ALL HOLD (exit 0). Positive control probe_1 (R1 standalone power distribution, symbolic/int exponents, factor count+order) HOLDS patched and is VIOLATED at base (prepatch_reproduced=true) — discriminating power confirmed.

Probe coverage: probe_1=R1.1-1.4; probe_2=R2.1/R2.2/R2.3 (only-nc-power, power+plain+scalar combine factor-by-factor with coefficient preserved); probe_3=R3.1/R3.2 (sum term-by-term incl. hidden-test-shaped TP(A,B)-TP(C,D)**x, plain addend unchanged); probe_4=R4.1 (non-TP base power reapplied, not distributed), R4.2 (bare TP & atom unchanged), R4.3 (helper tensor_product_simp_Pow returns non-Pow-of-TP input unchanged); probe_5=R5.1 (equal-length combine), R5.2 (commutator/anticommutator recursion), R5.4 (scalar pull-out), R2.5 (TypeError on non-TP/non-Pow-of-TP nc factor).

Weak candidate 'standalone_pow_only' (only patches the standalone-Pow branch, leaves tensor_product_simp_Mul and the helper alone) is REJECTED by probes 2,3,4,5 and passes only probe_1 — demonstrating the suite discriminates a plausible partial fix. Note during probe development I corrected probe_5's commutator expectation: SymPy's Commutator constructor canonicalizes/flips sign, so the correct assertion is r == Commutator(tps(arg0), tps(arg1)); after the fix probe_5 HOLDS on the patched tree. All required runs completed.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 5 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 5 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
weak.diff (standalone_pow_only) handles ONLY the standalone Pow case in tensor_product_simp (adds the TensorProduct-base branch) but leaves tensor_product_simp_Mul unchanged. It satisfies R1 (probe_1 HOLDS) yet is REJECTED by probe_2 (R2: powers of TPs inside a product -> TypeError, no combine), probe_3 (R3: TP(A,B)-TP(C,D)**x sum still fails because the Mul path in the sum's addend handling is unaffected only for the product case; actually the sum addend that is a pure Pow works but the mixed product does not — probe_3's second case TP(A,B)**2+TP(C,D) works, but the first case involving a subtraction where a term is a product path fails), probe_4 (R4.3: helper tensor_product_simp_Pow does not exist in this candidate -> ImportError), and probe_5 (R2.5 TypeError semantics differ). The suite thus discriminates this partial fix.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""R1: standalone power of a tensor product -> distribute exponent (symbolic & int).
POSITIVE CONTROL."""
from sympy import symbols
from sympy.physics.quantum.tensorproduct import TensorProduct as TP, tensor_product_simp as tps

A, B = symbols('A B', commutative=False)
x = symbols('x')

# symbolic exponent (R1.1, R1.2, R1.4)
r1 = tps(TP(A, B) ** x)
e1 = TP(A ** x, B ** x)
print("symbolic:", r1, "expected:", e1)

# positive integer exponent (R1.3)
r2 = tps(TP(A, B) ** 3)
e2 = TP(A ** 3, B ** 3)
print("int:", r2, "expected:", e2)

# preserve number & order of factors (R1.4): three factors
C = symbols('C', commutative=False)
r3 = tps(TP(A, B, C) ** x)
e3 = TP(A ** x, B ** x, C ** x)
print("three:", r3, "expected:", e3)

ok = (r1 == e1) and (r2 == e2) and (r3 == e3)
print("OK" if ok else "FAIL")
import sys
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Ran all 5 probes on the gold-PATCHED tree: ALL HOLD (exit 0). Positive control probe_1 (R1 standalone power distribution, symbolic/int exponents, factor count+order) HOLDS patched and is VIOLATED at base (prepatch_reproduced=true) — discriminating power confirmed.

Probe coverage: probe_1=R1.1-1.4; probe_2=R2.1/R2.2/R2.3 (only-nc-power, power+plain+scalar combine factor-by-factor with coefficient preserved); probe_3=R3.1/R3.2 (sum term-by-term incl. hidden-test-shaped TP(A,B)-TP(C,D)**x, plain addend unchanged); probe_4=R4.1 (non-TP base power reapplied, not distributed), R4.2 (bare TP & atom unchanged), R4.3 (helper tensor_product_simp_Pow returns non-Pow-of-TP input unchanged); probe_5=R5.1 (equal-length combine), R5.2 (commutator/anticommutator recursion), R5.4 (scalar pull-out), R2.5 (TypeError on non-TP/non-Pow-of-TP nc factor).

Weak candidate 'standalone_pow_only' (only patches the standalone-Pow branch, leaves tensor_product_simp_Mul and the helper alone) is REJECTED by probes 2,3,4,5 and passes only probe_1 — demonstrating the suite discriminates a plausible partial fix. Note during probe development I corrected probe_5's commutator expectation: SymPy's Commutator constructor canonicalizes/flips sign, so the correct assertion is r == Commutator(tps(arg0), tps(arg1)); after the fix probe_5 HOLDS on the patched tree. All required runs completed.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the correct modeling boundary: the changed observable behavior of tensor_product_simp evaluating powers of TensorProduct (via new helper tensor_product_simp_Pow and the extended Pow/Mul/Add branches), not a narrow slice. The gold patch adds exactly: (a) Pow branch in tensor_product_simp distributing exponent over TP factors when base is a TensorProduct, else simplify-base**exp (R1/R4.1); (b) tensor_product_simp_Pow helper distributing e.exp over base.args, returning input unchanged otherwise (R4.3); (c) Mul handling of Pow-of-TP factors, scalar preservation, and TypeError on non-TP/non-Pow-of-TP nc factors (R2); (d) Add recursion is pre-existing and preserved (R3.1). R5 regression claims map to unchanged code paths. No requirement mandates behavior the patch lacks, forbids behavior it has, or invents behavior. FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe behavior (distribute exponent across TP factors for standalone powers, powers within products with scalars/plain TPs, and powers within sums; leave non-TP powers unchanged; regression protection). This aligns with the four hidden assertions in test_tensor_product_simp but transmits none of them: no test file/function name, no quoted test or gold code, no test symbols (A,B,C,D)/TP alias, no parametrization ids. The fix-invented helper `tensor_product_simp_Pow` is never named — only referred to abstractly as 'the helper that distributes an exponent' (Req 4.3). Named functions `tensor_product_simp`/`tensor_product_simp_Mul` are pre-existing public API (legitimate localization). Symbolic (`x`)/integer(`2`) exponents and two-factor TPs are generic and already implied by the public problem_statement's `**n`/`tp(1,1)` examples. Req 2.5's TypeError reflects pre-existing code behavior, not a test/gold-only artifact (no test checks it). This is the intended translation of test-verified behavior into an EARS spec, not test reconstruction.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
