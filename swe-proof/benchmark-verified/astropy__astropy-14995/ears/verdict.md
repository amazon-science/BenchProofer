# P2 adversarial audit — astropy__astropy-14995

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
The weak candidate patch (wrap handle_mask call in try/except TypeError -> return None) stops the base-tree crash but returns mask=None instead of propagating the single present mask. Probe_1 (self-masked + unmasked operand, bitwise_or) observed result.mask=None, expected [1 0 1]; probe_2 (masked operand * scalar) observed None. Both REJECT the candidate, so it would not resolve F2P test_nddata_bitmask_arithmetic which asserts the propagated mask equals the present mask.
```

**Attacks re-run (5):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control / Req1.3: self has integer bitmask, operand has no mask,
handle_mask=np.bitwise_or -> no raise; result.mask == the present mask."""
import numpy as np
from astropy.nddata import NDDataRef

m = np.array([1, 0, 1], dtype=int)
a = NDDataRef(np.array([1, 2, 3]), mask=m.copy())
b = NDDataRef(np.array([4, 5, 6]))  # no mask
try:
    res = a.add(b, handle_mask=np.bitwise_or)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    raise SystemExit(1)
print("result mask:", res.mask)
ok = res.mask is not None and np.array_equal(res.mask, m)
print("equals present mask:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req1.4: masked operand combined with a plain scalar/constant -> no TypeError,
result.mask equals the present mask."""
import numpy as np
from astropy.nddata import NDDataRef

m = np.array([1, 0, 1], dtype=int)
a = NDDataRef(np.array([1, 2, 3]), mask=m.copy())
try:
    res = a.multiply(3, handle_mask=np.bitwise_or)
except TypeError as e:
    print("RAISED TypeError:", e)
    raise SystemExit(1)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    raise SystemExit(1)
print("scalar-op result mask:", res.mask)
ok = res.mask is not None and np.array_equal(res.mask, m)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req1.2 & Req1.5: self has NO mask, operand HAS a mask -> result mask is a
copy of operand's mask; and the propagated mask is an independent copy
(mutating the result does not alter the source operand's mask)."""
import numpy as np
from astropy.nddata import NDDataRef

m = np.array([0, 1, 1], dtype=int)
a = NDDataRef(np.array([1, 2, 3]))          # no mask
b = NDDataRef(np.array([4, 5, 6]), mask=m.copy())
try:
    res = a.add(b, handle_mask=np.bitwise_or)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    raise SystemExit(1)
print("result mask:", res.mask)
if res.mask is None or not np.array_equal(res.mask, m):
    print("mask not propagated from operand")
    raise SystemExit(1)
# independence: mutate result mask, operand mask must be unchanged
res.mask[0] = 99
indep = np.array_equal(b.mask, m)
print("operand mask after mutating result:", b.mask, "independent:", indep)
raise SystemExit(0 if indep else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req2.2: both operands carry masks with handle_mask=np.bitwise_or ->
result.mask == element-wise bitwise-or of the two masks.
Also Req3.3: both unmasked with bitwise_or -> result.mask is None."""
import numpy as np
from astropy.nddata import NDDataRef

m1 = np.array([1, 0, 2, 0], dtype=int)
m2 = np.array([0, 4, 2, 0], dtype=int)
a = NDDataRef(np.array([1, 2, 3, 4]), mask=m1.copy())
b = NDDataRef(np.array([5, 6, 7, 8]), mask=m2.copy())
res = a.add(b, handle_mask=np.bitwise_or)
expected = np.bitwise_or(m1, m2)
print("both-mask result:", res.mask, "expected:", expected)
if res.mask is None or not np.array_equal(res.mask, expected):
    raise SystemExit(1)

# neither has a mask, bitwise_or supplied -> None
c = NDDataRef(np.array([1, 2, 3]))
d = NDDataRef(np.array([4, 5, 6]))
res2 = c.add(d, handle_mask=np.bitwise_or)
print("neither-mask result:", res2.mask)
if res2.mask is not None:
    raise SystemExit(1)
raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req4.1: 'first_found'/'ff' semantics preserved: when at least one operand has
a mask, result mask is a copy of the first operand's mask if it exists, else the
other operand's mask. Req3.2: handle_mask=None -> result mask is None."""
import numpy as np
from astropy.nddata import NDDataRef

m1 = np.array([1, 0, 1], dtype=int)
m2 = np.array([0, 1, 0], dtype=int)

# both masks: first_found returns first operand's mask
a = NDDataRef(np.array([1, 2, 3]), mask=m1.copy())
b = NDDataRef(np.array([4, 5, 6]), mask=m2.copy())
for opt in ("first_found", "ff"):
    r = a.add(b, handle_mask=opt)
    print(opt, "both ->", r.mask)
    if not np.array_equal(r.mask, m1):
        raise SystemExit(1)

# only second has a mask: first_found returns the other operand's mask
a2 = NDDataRef(np.array([1, 2, 3]))
b2 = NDDataRef(np.array([4, 5, 6]), mask=m2.copy())
r2 = a2.add(b2, handle_mask="first_found")
print("ff only-operand ->", r2.mask)
if r2.mask is None or not np.array_equal(r2.mask, m2):
    raise SystemExit(1)

# handle_mask=None -> None even with masks present
r3 = a.add(b, handle_mask=None)
print("handle_mask None ->", r3.mask)
if r3.mask is not None:
    raise SystemExit(1)
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control / Req1.3: self has integer bitmask, operand has no mask,
handle_mask=np.bitwise_or -> no raise; result.mask == the present mask."""
import numpy as np
from astropy.nddata import NDDataRef

m = np.array([1, 0, 1], dtype=int)
a = NDDataRef(np.array([1, 2, 3]), mask=m.copy())
b = NDDataRef(np.array([4, 5, 6]))  # no mask
try:
    res = a.add(b, handle_mask=np.bitwise_or)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    raise SystemExit(1)
print("result mask:", res.mask)
ok = res.mask is not None and np.array_equal(res.mask, m)
print("equals present mask:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance astropy-14995: regression where _arithmetic_mask invokes handle_mask even when one operand lacks a mask, raising TypeError with np.bitwise_or. Gold fix changes `elif operand is None` to test `operand.mask is None`.

Probe->requirement mapping and results (PATCHED / BASE / WEAK):
- probe_1 = Req1.1/1.3 + positive control: self-masked, operand unmasked, bitwise_or -> no raise, result.mask==present mask. PATCHED HOLD / BASE FAIL(TypeError) / WEAK FAIL(None).
- probe_2 = Req1.4: masked operand combined with plain scalar (multiply,3) -> no TypeError, mask preserved. PATCHED HOLD / BASE FAIL(TypeError) / WEAK FAIL(None).
- probe_3 = Req1.2 + Req1.5: self unmasked, operand masked -> result mask copy of operand mask AND independent (mutating result doesn't touch operand). PATCHED HOLD / BASE HOLD (this branch already worked at base) / WEAK HOLD.
- probe_4 = Req2.2 + Req3.3: both masked with bitwise_or -> element-wise OR; neither masked -> None. PATCHED HOLD / BASE HOLD / WEAK HOLD.
- probe_5 = Req4.1 + Req3.2: first_found/ff copy first-operand-else-other mask; handle_mask=None -> None. PATCHED HOLD / BASE HOLD / WEAK HOLD.

Discriminating power: positive control probe_1 (and probe_2) fail at base with the exact documented TypeError and hold on patched. The requirements-plausible-but-wrong 'swallow TypeError' candidate is rejected by probes 1&2 because it violates the SHALL that the single present mask be propagated. Suite discriminates wrong implementations. Verdict SOUND.

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
The weak candidate patch (wrap handle_mask call in try/except TypeError -> return None) stops the base-tree crash but returns mask=None instead of propagating the single present mask. Probe_1 (self-masked + unmasked operand, bitwise_or) observed result.mask=None, expected [1 0 1]; probe_2 (masked operand * scalar) observed None. Both REJECT the candidate, so it would not resolve F2P test_nddata_bitmask_arithmetic which asserts the propagated mask equals the present mask.
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
"""Positive control / Req1.3: self has integer bitmask, operand has no mask,
handle_mask=np.bitwise_or -> no raise; result.mask == the present mask."""
import numpy as np
from astropy.nddata import NDDataRef

m = np.array([1, 0, 1], dtype=int)
a = NDDataRef(np.array([1, 2, 3]), mask=m.copy())
b = NDDataRef(np.array([4, 5, 6]))  # no mask
try:
    res = a.add(b, handle_mask=np.bitwise_or)
except Exception as e:
    print("RAISED:", type(e).__name__, e)
    raise SystemExit(1)
print("result mask:", res.mask)
ok = res.mask is not None and np.array_equal(res.mask, m)
print("equals present mask:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance astropy-14995: regression where _arithmetic_mask invokes handle_mask even when one operand lacks a mask, raising TypeError with np.bitwise_or. Gold fix changes `elif operand is None` to test `operand.mask is None`.

Probe->requirement mapping and results (PATCHED / BASE / WEAK):
- probe_1 = Req1.1/1.3 + positive control: self-masked, operand unmasked, bitwise_or -> no raise, result.mask==present mask. PATCHED HOLD / BASE FAIL(TypeError) / WEAK FAIL(None).
- probe_2 = Req1.4: masked operand combined with plain scalar (multiply,3) -> no TypeError, mask preserved. PATCHED HOLD / BASE FAIL(TypeError) / WEAK FAIL(None).
- probe_3 = Req1.2 + Req1.5: self unmasked, operand masked -> result mask copy of operand mask AND independent (mutating result doesn't touch operand). PATCHED HOLD / BASE HOLD (this branch already worked at base) / WEAK HOLD.
- probe_4 = Req2.2 + Req3.3: both masked with bitwise_or -> element-wise OR; neither masked -> None. PATCHED HOLD / BASE HOLD / WEAK HOLD.
- probe_5 = Req4.1 + Req3.2: first_found/ff copy first-operand-else-other mask; handle_mask=None -> None. PATCHED HOLD / BASE HOLD / WEAK HOLD.

Discriminating power: positive control probe_1 (and probe_2) fail at base with the exact documented TypeError and hold on patched. The requirements-plausible-but-wrong 'swallow TypeError' candidate is rejected by probes 1&2 because it violates the SHALL that the single present mask be propagated. Suite discriminates wrong implementations. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed on gold-patched tree: _arithmetic_mask source confirms the `elif operand.mask is None: return deepcopy(self.mask)` branch. Comprehensive behavioral probe (p4.py) covering all 4 requirements' acceptance criteria returned ALL PASS. Requirement boundary correctly pins the changed observable mask-combination behavior, not just one helper/branch.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements are entirely reconstructible from the PUBLIC problem_statement plus legitimate code localization. The problem_statement already contains the full reproduction: the same NDDataRef, handle_mask=np.bitwise_or, and all four case combinations (no-mask*constant, no-mask*self, mask*constant, mask*self, mask*no-mask) with expected results (None vs. copied mask vs. TypeError). The requirements' case enumeration (Req 1-3) mirrors those PUBLIC cases and the maintainer's PR discussion in the issue, not the hidden parametrization. Naming `NDArithmeticMixin._arithmetic_mask` / `_arithmetic` and the public methods add/subtract/multiply/divide is legitimate localization — these are the actual changed symbols, and the gold edit's branch structure (self.mask None / operand.mask None / else handle_mask) is standard behavioral description, not quoted test code. No test function name (test_nddata_bitmask_arithmetic), no test file path, no parametrization ids, no fix-invented identifiers appear. The only detail not in problem_statement is the handle_mask string options 'first_found'/'ff' (Req 4.1); these are pre-existing public API options being described as preserved behavior (the fix invents nothing here), not a reconstruction of the hidden test — this is describing existing documented behavior, which is legitimate. The specific test arrays ([[0,1,64],[8,0,1],[2,1,0]] etc.) are NOT reproduced in the requirements; they are described abstractly as 'integer bit-mask'. No hidden-test/gold content is transmitted beyond the public spec.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
