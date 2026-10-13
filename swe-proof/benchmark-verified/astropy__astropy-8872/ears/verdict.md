# P2 adversarial audit — astropy__astropy-8872

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import astropy.units as u

# R1.1 (positive control): float16 input preserved, no explicit dtype
q = np.float16(1) * u.km
print("float16 -> dtype:", q.dtype)
ok = q.dtype == np.dtype(np.float16)
sys.exit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import astropy.units as u

# R1.2 / R1.3: float32, float64, float128 preserved
oks = []
for t in [np.float32, np.float64]:
    q = u.Quantity(np.array([1, 2, 3], dtype=t), u.m)
    print(t, "->", q.dtype)
    oks.append(q.dtype == np.dtype(t))
if hasattr(np, "float128"):
    q = u.Quantity(np.array([1, 2, 3], dtype=np.float128), u.m)
    print("float128 ->", q.dtype)
    oks.append(q.dtype == np.dtype(np.float128))
sys.exit(0 if all(oks) else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import astropy.units as u

# R1.4: complex element types preserved
oks = []
for t in [np.complex64, np.complex128]:
    q = u.Quantity(np.array([1, 2], dtype=t), u.m)
    print(t, "->", q.dtype)
    oks.append(q.dtype == np.dtype(t))
sys.exit(0 if all(oks) else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import astropy.units as u

# R2.1: integer (signed/unsigned) coerced to default float (float64)
oks = []
for t in [np.int16, np.int32, np.int64, np.uint8, np.uint32]:
    q = u.Quantity(np.array([1, 2, 3], dtype=t), u.m)
    print(t, "->", q.dtype)
    oks.append(q.dtype == np.dtype(float))
sys.exit(0 if all(oks) else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
import sys
import decimal
import numpy as np
import astropy.units as u

# R2.2: object dtype (decimal.Decimal) coerced to default float on general path
q = u.Quantity(decimal.Decimal('10.25'), u.m)
print("Decimal -> dtype:", q.dtype)
ok = q.dtype == np.dtype(float)
sys.exit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import astropy.units as u

# R2.3: explicit dtype respected, no default coercion
oks = []
# integer input with explicit int dtype stays int
q = u.Quantity(np.array([1, 2, 3], dtype=np.int32), u.m, dtype=np.int32)
print("int32 explicit ->", q.dtype)
oks.append(q.dtype == np.dtype(np.int32))
# float16 input forced to float32
q2 = u.Quantity(np.float16(1), u.m, dtype=np.float32)
print("float16 forced float32 ->", q2.dtype)
oks.append(q2.dtype == np.dtype(np.float32))
sys.exit(0 if all(oks) else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import astropy.units as u

# R3: fast path (input already a Quantity) — float16 preserved, integer coerced
src16 = u.Quantity(np.float16(2), u.m)
q = u.Quantity(src16)  # reuse on fast path, no explicit dtype
print("Quantity(float16 Quantity) ->", q.dtype)
ok1 = q.dtype == np.dtype(np.float16)

src_int = u.Quantity(np.array([1, 2, 3], dtype=np.int32), u.m, dtype=np.int32)
q2 = u.Quantity(src_int)
print("Quantity(int32 Quantity) ->", q2.dtype)
ok2 = q2.dtype == np.dtype(float)

sys.exit(0 if (ok1 and ok2) else 1)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
import sys
import numpy as np
import astropy.units as u

# R4.2: unparseable / non-numeric input raises TypeError; R4.1 lists/scalars work
oks = []
try:
    u.Quantity("not a number", u.m)
    print("no error raised")
    oks.append(False)
except TypeError as e:
    print("TypeError raised:", e)
    oks.append(True)

# R4.1 regression: python int list coerced to float; python float list preserved kind
q = u.Quantity([1, 2, 3], u.m)
print("list int ->", q.dtype)
oks.append(q.dtype == np.dtype(float))
sys.exit(0 if all(oks) else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
import numpy as np
import astropy.units as u

# R1.1 (positive control): float16 input preserved, no explicit dtype
q = np.float16(1) * u.km
print("float16 -> dtype:", q.dtype)
ok = q.dtype == np.dtype(np.float16)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: preserve all float/complex element dtypes (incl float16) in Quantity.__new__, coerce integer+object inputs to float64, apply the fix consistently on both the general path and the unit-carrying fast path; keep TypeError for unparseable input and other construction behavior.

Probes (all HOLD on gold-patched tree, exit 0):
- probe_1 (R1.1, POSITIVE CONTROL): float16 scalar*u.km -> float16. Base FAILS (float64), patched HOLDS -> discriminates.
- probe_2 (R1.2/R1.3): float32/float64/float128 preserved.
- probe_3 (R1.4): complex64/complex128 preserved.
- probe_4 (R2.1): int16/int32/int64/uint8/uint32 -> float64.
- probe_5 (R2.2): decimal.Decimal (object dtype) -> float64.
- probe_6 (R2.3): explicit dtype respected (int32 kept as int32; float16 forced to float32), no default coercion.
- probe_7 (R3.1/R3.2, also secondary positive control): fast path with Quantity input keeps float16, coerces int32 Quantity -> float64. Base FAILS -> discriminates.
- probe_8 (R4.1/R4.2): unparseable string raises TypeError; python int list -> float64.

Weak candidate 'general_path_only': applies the gold change ONLY to the general construction path (kind in 'iuO') but leaves the fast path's original can_cast test untouched. This is the lazy/partial fix a weak reading permits (issue text focuses on scalar float16). It is REJECTED by probe_7 (float16 Quantity re-wrapped -> float64), demonstrating the suite discriminates wrong implementations that violate R3. All other probes still hold under it, confirming R3-specific discriminating power.

Verdict SOUND: 8 distinct probes covering all 4 requirements hold on the patched tree; positive control discriminates base vs patched (float16 upgraded to float64 at base); >=1 requirements-adjacent wrong candidate exercised and REJECTED. No violation found; requirements are neither too strong nor (per the fast-path probe) too weak on the R3 axis.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
import sys
import numpy as np
import astropy.units as u

# R1.1 (positive control): float16 input preserved, no explicit dtype
q = np.float16(1) * u.km
print("float16 -> dtype:", q.dtype)
ok = q.dtype == np.dtype(np.float16)
sys.exit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Requirements: preserve all float/complex element dtypes (incl float16) in Quantity.__new__, coerce integer+object inputs to float64, apply the fix consistently on both the general path and the unit-carrying fast path; keep TypeError for unparseable input and other construction behavior.

Probes (all HOLD on gold-patched tree, exit 0):
- probe_1 (R1.1, POSITIVE CONTROL): float16 scalar*u.km -> float16. Base FAILS (float64), patched HOLDS -> discriminates.
- probe_2 (R1.2/R1.3): float32/float64/float128 preserved.
- probe_3 (R1.4): complex64/complex128 preserved.
- probe_4 (R2.1): int16/int32/int64/uint8/uint32 -> float64.
- probe_5 (R2.2): decimal.Decimal (object dtype) -> float64.
- probe_6 (R2.3): explicit dtype respected (int32 kept as int32; float16 forced to float32), no default coercion.
- probe_7 (R3.1/R3.2, also secondary positive control): fast path with Quantity input keeps float16, coerces int32 Quantity -> float64. Base FAILS -> discriminates.
- probe_8 (R4.1/R4.2): unparseable string raises TypeError; python int list -> float64.

Weak candidate 'general_path_only': applies the gold change ONLY to the general construction path (kind in 'iuO') but leaves the fast path's original can_cast test untouched. This is the lazy/partial fix a weak reading permits (issue text focuses on scalar float16). It is REJECTED by probe_7 (float16 Quantity re-wrapped -> float64), demonstrating the suite discriminates wrong implementations that violate R3. All other probes still hold under it, confirming R3-specific discriminating power.

Verdict SOUND: 8 distinct probes covering all 4 requirements hold on the patched tree; positive control discriminates base vs patched (float16 upgraded to float64 at base); >=1 requirements-adjacent wrong candidate exercised and REJECTED. No violation found; requirements are neither too strong nor (per the fast-path probe) too weak on the R3 axis.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch replaces the can_cast(float32,...) test with element-kind checks: general path coerces kind in 'iuO' to float; fast path (unit-carrying input) coerces kind in 'iu'. Probe on gold-patched image confirms exact match to every requirement:
- R1.1 float16->float16 (was float64 at base — the bug fix). R1.2 float32->float32. R1.3 float64->float64. R1.4 complex64 preserved (complex64), preservation independent of can-hold-float32. ALL HOLD.
- R2.1 int32->float64, uint8->float64. R2.2 object/decimal.Decimal->float64 on GENERAL path. R2.3 explicit dtype=int32 respected (stays int32, no coercion). ALL HOLD.
- R3.1 fast-path Quantity(float16-Quantity)->float16 preserved; fast-path complex preserved. R3.2 fast-path int Quantity->float64. R3.3 both branches decide by element-type category. ALL HOLD.
- R4 regression clauses are consistent with unchanged surrounding code.
The one behavior the requirements never mention is bool: base coerced bool->float64, patched code PRESERVES bool (kind 'b' excluded from both 'iu' and 'iuO'); docstring dropped 'bool' from the coercion list. This is a SILENCE, not a contradiction — R4.1 states coercion applies 'only to integer and object inputs', which exactly matches the code (bool preserved). No requirement asserts bool->float64, so no requirement diverges. That is an adequacy/completeness gap, not a faithfulness break. R2.2 correctly scopes object-dtype coercion to 'the general construction path' (patch adds 'O' only to the general-path branch, not the fast path), and my probe confirms the fast path uses 'iu'. Requirements pin the changed observable behavior (dtype preservation vs coercion) at the right boundary, not a narrow slice. Verdict FAITHFUL. (Separate note: G-PANEL-3 leakage — R2.2's decimal.Decimal example traces to hidden F2P test — is out of scope for the faithfulness gate.)

- R1.1 float16->float16 (was float64 at base — the bug fix). R1.2 float32->float32. R1.3 float64->float64. R1.4 complex64 preserved (complex64), preservation independent of can-hold-float32. ALL HOLD.
- R2.1 int32->float64, uint8->float64. R2.2 object/decimal.Decimal->float64 on GENERAL path. R2.3 explicit dtype=int32 respected (stays int32, no coercion). ALL HOLD.
- R3.1 fast-path Quantity(float16-Quantity)->float16 preserved; fast-path complex preserved. R3.2 fast-path int Quantity->float64. R3.3 both branches decide by element-type category. ALL HOLD.
- R4 regression clauses are consistent with unchanged surrounding code.
The one behavior the requirements never mention is bool: base coerced bool->float64, patched code PRESERVES bool (kind 'b' excluded from both 'iu' and 'iuO'); docstring dropped 'bool' from the coercion list. This is a SILENCE, not a contradiction — R4.1 states coercion applies 'only to integer and object inputs', which exactly matches the code (bool preserved). No requirement asserts bool->float64, so no requirement diverges. That is an adequacy/completeness gap, not a faithfulness break. R2.2 correctly scopes object-dtype coercion to 'the general construction path' (patch adds 'O' only to the general-path branch, not the fast path), and my probe confirms the fast path uses 'iu'. Requirements pin the changed observable behavior (dtype preservation vs coercion) at the right boundary, not a narrow slice. Verdict FAITHFUL. (Separate note: G-PANEL-3 leakage — R2.2's decimal.Decimal example traces to hidden F2P test — is out of scope for the faithfulness gate.)


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements document describes the behavioral contract of Quantity.__new__ (preserve float16/32/64/128 and complex, coerce integer/object inputs to float) and localizes the change to the two constructor decision points (general path + unit-carrying fast path). All of this is either public in the problem_statement (which itself shows the float16/float32/float64/float128 examples and the upgrade bug) or is legitimate localization derivable from reading quantity.py. No test file path, test class/function name (TestQuantityCreation::test_preserve_dtype), parametrization ids, verbatim gold lines (e.g. `value.dtype.kind in 'iu'` / `'iuO'`), or fix-invented identifiers appear. The one item present in the hidden test but not the problem_statement is the `decimal.Decimal` object-dtype coercion (Req 2.2), but it is used as an illustrative canonical stdlib example of an object-dtype input to describe genuine gold-patch behavior (the 'O' kind), not as a quoted test value/name — it translates behavior rather than transmitting the test. Enumerations (float16/32/64/128) match the PUBLIC problem statement, not a private test parametrization (the hidden test is not parametrized). No semantic gold/test reconstruction.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
