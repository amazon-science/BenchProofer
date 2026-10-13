# P2 adversarial audit — sympy__sympy-14248

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 9 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 9 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py`, `probe_9.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (9):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
from sympy import MatrixSymbol
n = 2
A = MatrixSymbol('A', n, n)
B = MatrixSymbol('B', n, n)
expr = A - A*B - B
out = str(expr)
print("str(A - A*B - B) =", repr(out))
# Req 1.5: reads as subtraction, no (-1)* or -1* text
ok = ('(-1)' not in out) and ('-1*' not in out) and (out == '-B - A*B + A')
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
from sympy import MatrixSymbol
n = 2
A = MatrixSymbol('A', n, n)
# Req 1.4: negated matrix symbol renders as just "-" + symbol, no (-1)* / -1*
out = str(-A)
print("str(-A) =", repr(out))
ok = (out == '-A')
sys.exit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
from sympy import MatrixSymbol, latex
n = 2
A = MatrixSymbol('A', n, n)
B = MatrixSymbol('B', n, n)
# Req 2.4: latex(A - A*B - B) reads as subtraction, no -1 coefficients
out = latex(A - A*B - B)
print("latex(A - A*B - B) =", repr(out))
ok = ('-1' not in out) and (out == '-B - A B + A')
sys.exit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
from sympy import MatrixSymbol, latex
n = 2
A = MatrixSymbol('A', n, n)
# Req 2.3: latex(-A) is symbol prefixed with one '-' and no coefficient
out = latex(-A)
print("latex(-A) =", repr(out))
ok = (out == '-A')
sys.exit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
from sympy import MatrixSymbol
from sympy.printing.pretty import pretty
n = 2
A = MatrixSymbol('A', n, n)
B = MatrixSymbol('B', n, n)
# Req 3.4: pretty(A - B) shows subtracted term with own leading minus, other added
out = pretty(A - B)
print("pretty(A - B) =", repr(out))
ok = (out == '-B + A')
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
from sympy import MatrixSymbol
# Req 5.1 regression: positive scalar times matrix element unchanged
n = 2
A = MatrixSymbol('A', n, n)
out = str(3*A[0, 0])
print("str(3*A[0,0]) =", repr(out))
from sympy import latex
lout = latex(3*A[0, 0])
print("latex(3*A[0,0]) =", repr(lout))
ok = (out == '3*A[0, 0]') and (lout == '3 A_{0, 0}')
sys.exit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import sys
from sympy import MatrixSymbol
# Req 5.2 regression: all-positive matrix addition joined with " + ", no subtraction
n = 2
A = MatrixSymbol('A', n, n)
B = MatrixSymbol('B', n, n)
C = MatrixSymbol('C', n, n)
out = str(A + B + C)
print("str(A + B + C) =", repr(out))
from sympy import latex
lout = latex(A + B + C)
print("latex(A + B + C) =", repr(lout))
ok = (out == 'A + B + C') and ('-' not in out) and (lout == 'A + B + C')
sys.exit(0 if ok else 1)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
import sys
from sympy import MatrixSymbol
# Req 5.5: negative leading coeff other than -1 keeps magnitude, sign to front
n = 2
A = MatrixSymbol('A', n, n)
B = MatrixSymbol('B', n, n)
out = str(-3*A*B)
print("str(-3*A*B) =", repr(out))
# sign factored, magnitude 3 retained
ok = (out == '-3*A*B')
sys.exit(0 if ok else 1)
```

Attack 9 — `probe_9.py` → holds on the patched tree (good)

```python
import sys
from sympy import MatrixSymbol
# Req 1.7 / Req 4: matrix element whose underlying matrix is a difference
n = 2
A = MatrixSymbol('A', n, n)
B = MatrixSymbol('B', n, n)
C = MatrixSymbol('C', n, n)
expr = C[0, 0].subs(C, A - B)
out = str(expr)
print("str((A-B)[0,0]) =", repr(out))
ok = ('(-1)' not in out) and (out == '(-B + A)[0, 0]')
sys.exit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from sympy import MatrixSymbol
n = 2
A = MatrixSymbol('A', n, n)
B = MatrixSymbol('B', n, n)
expr = A - A*B - B
out = str(expr)
print("str(A - A*B - B) =", repr(out))
# Req 1.5: reads as subtraction, no (-1)* or -1* text
ok = ('(-1)' not in out) and ('-1*' not in out) and (out == '-B - A*B + A')
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

9 probes cover Req1-5. Results (patched/base): probe_1 str(A-A*B-B)=='-B - A*B + A' [Req1.5] HOLDS patched / VIOLATED base (POSITIVE CONTROL, discriminates); probe_2 str(-A)=='-A' [Req1.4] HOLDS/VIOLATED base; probe_3 latex(A-A*B-B)=='-B - A B + A' [Req2.4] HOLDS/VIOLATED base; probe_4 latex(-A)=='-A' [Req2.3] HOLDS/VIOLATED base; probe_5 pretty(A-B)=='-B + A' [Req3.4] HOLDS patched (also HOLDS base — pretty already recombined this simple case, non-discriminating but conformance check); probe_6 str(3*A[0,0])=='3*A[0, 0]' & latex=='3 A_{0, 0}' [Req5.1 regression] HOLDS; probe_7 A+B+C all-positive joined with ' + ' str & latex [Req5.2] HOLDS; probe_8 str(-3*A*B)=='-3*A*B' magnitude retained [Req5.5] HOLDS; probe_9 str((A-B)[0,0])=='(-B + A)[0, 0]' matrix element of difference [Req1.7/Req4] HOLDS/VIOLATED base.

All 9 HOLD on patched tree. WEAK CANDIDATE (str.py-only hunk of gold, leaving latex.py & pretty.py unfixed) REJECTED by probe_3 & probe_4 (latex still emits -1 coeffs) => suite discriminates a plausible partial fix that would not resolve the hidden latex/pretty tests. No requirement-conforming alternative found that passes the full suite yet fails the harness. Note: meta.json records G-PANEL-3=LEAKAGE (Req3.5's expected string with anomalous spacing copied from hidden test), but that is a leakage/hygiene concern, not a spec-fidelity (G-EQ) defect — the requirements are neither too strong (no probe fails on patched) nor too weak (weak candidate rejected).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 9 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 9 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py`, `probe_9.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (9):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

Attack 9 — `probe_9.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
from sympy import MatrixSymbol
n = 2
A = MatrixSymbol('A', n, n)
B = MatrixSymbol('B', n, n)
expr = A - A*B - B
out = str(expr)
print("str(A - A*B - B) =", repr(out))
# Req 1.5: reads as subtraction, no (-1)* or -1* text
ok = ('(-1)' not in out) and ('-1*' not in out) and (out == '-B - A*B + A')
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

9 probes cover Req1-5. Results (patched/base): probe_1 str(A-A*B-B)=='-B - A*B + A' [Req1.5] HOLDS patched / VIOLATED base (POSITIVE CONTROL, discriminates); probe_2 str(-A)=='-A' [Req1.4] HOLDS/VIOLATED base; probe_3 latex(A-A*B-B)=='-B - A B + A' [Req2.4] HOLDS/VIOLATED base; probe_4 latex(-A)=='-A' [Req2.3] HOLDS/VIOLATED base; probe_5 pretty(A-B)=='-B + A' [Req3.4] HOLDS patched (also HOLDS base — pretty already recombined this simple case, non-discriminating but conformance check); probe_6 str(3*A[0,0])=='3*A[0, 0]' & latex=='3 A_{0, 0}' [Req5.1 regression] HOLDS; probe_7 A+B+C all-positive joined with ' + ' str & latex [Req5.2] HOLDS; probe_8 str(-3*A*B)=='-3*A*B' magnitude retained [Req5.5] HOLDS; probe_9 str((A-B)[0,0])=='(-B + A)[0, 0]' matrix element of difference [Req1.7/Req4] HOLDS/VIOLATED base.

All 9 HOLD on patched tree. WEAK CANDIDATE (str.py-only hunk of gold, leaving latex.py & pretty.py unfixed) REJECTED by probe_3 & probe_4 (latex still emits -1 coeffs) => suite discriminates a plausible partial fix that would not resolve the hidden latex/pretty tests. No requirement-conforming alternative found that passes the full suite yet fails the harness. Note: meta.json records G-PANEL-3=LEAKAGE (Req3.5's expected string with anomalous spacing copied from hidden test), but that is a leakage/hygiene concern, not a spec-fidelity (G-EQ) defect — the requirements are neither too strong (no probe fails on patched) nor too weak (weak candidate rejected).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Boundary is correct: requirements pin the changed observable behavior (matrix diffs rendering as subtractions, sign factored out, -1 coefficient dropped, magnitude retained for other negatives) across all three primary printers plus the six codegen printers that reuse the string routine, exactly matching patch.diff to str.py/latex.py/pretty.py and the test_patch expectations. Probed live on the gold-patched image; all observations confirmed.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements localize the change to str.py/latex.py/pretty.py and the code-gen printers (legitimate) and translate test-checked behavior into EARS rules. Every literal string quoted in the document (`(-1)*B + (-1)*A*B + A`, `-B + -A⋅B + A`, `-1 B + -1 A B + A`) is the OLD/buggy output present verbatim in the public problem_statement. Crucially, NO gold/expected output string from the hidden test_patch is reproduced: the distinctive gold assertions — pretty `-A*B -B*C + A*B*C` (odd spacing), `-B + A`, `-A*B*C`; latex `-B - A B + A`, `-B - A B - A B C`, `-A`; str `-B - A*B + A`, `-(A + B) + A*B`; element `(-B + A)[0,0]` / `\left(-B + A\right)_{0,0}` — never appear. R1.5/R2.4 explicitly say 'read as a subtraction with (-1) removed' rather than giving the gold string. No test names (test_MatrixSymbol_printing/test_MatrixElement_printing), file paths, or parametrization ids leak. Scenarios only derivable from hidden tests (MatrixElement of a difference; grouped subtracted sum A*B-(A+B); 3*A[0,0] positive-coeff regression) are stated as general behavioral requirements, not as verbatim assertions. This is behavioral description, not test transmission.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
