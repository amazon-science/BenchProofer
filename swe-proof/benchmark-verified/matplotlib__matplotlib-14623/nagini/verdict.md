# P2 adversarial audit — matplotlib__matplotlib-14623

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_2.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying same-spec wrong impl produces a faithful patch that fails to resolve. The spec pins distinct-input output EXACTLY: Ensures(Implies(lo != hi, Result()[0] == lo and Result()[1] == hi)). Hence on every tested distinct pair (F2P: set_yscale('log'); set_ylim(10,1); expects (10,1); all P2P set_*lim calls use distinct admissible endpoints) any verifying impl coincides with the gold-patched code. The only behavioral freedom the spec leaves is (a) the equal/singular-endpoint expansion magnitude (spec requires only Result()[0] < Result()[1]) and (b) whether the conditioning callee is actually invoked on distinct admissible inputs (where nonsingular+limit_range_for_scale are value-preserving no-ops). Neither is observed by any FAIL_TO_PASS or PASS_TO_PASS assertion, so all three verifying candidates' faithful patches RESOLVE.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # orientation-preserving case) or equal (the singular case that the
     # conditioning expands).
     Requires(lo > 0 and hi > 0 and lo < 1000000000000000 and hi < 1000000000000000)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # When the requested endpoints are distinct, the stored interval keeps the
@@ -117,15 +115,7 @@
     Ensures(Implies(lo == hi, Result()[0] < Result()[1]))
     # post-conditions-end
     # impl-start
-    swapped = lo > hi
     a = conditioned_lo(lo, hi)
     b = conditioned_hi(lo, hi)
-    # The conditioning normalises to strictly ascending order; the requested
-    # orientation, captured before conditioning, is restored afterwards.
-    if swapped:
-        # caller requested descending: restore the requested orientation.
-        tmp = a
-        a = b
-        b = tmp
     return (a, b)
     # impl-end
```

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # orientation-preserving case) or equal (the singular case that the
     # conditioning expands).
     Requires(lo > 0 and hi > 0 and lo < 1000000000000000 and hi < 1000000000000000)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # When the requested endpoints are distinct, the stored interval keeps the
@@ -117,15 +115,9 @@
     Ensures(Implies(lo == hi, Result()[0] < Result()[1]))
     # post-conditions-end
     # impl-start
-    swapped = lo > hi
-    a = conditioned_lo(lo, hi)
-    b = conditioned_hi(lo, hi)
-    # The conditioning normalises to strictly ascending order; the requested
-    # orientation, captured before conditioning, is restored afterwards.
-    if swapped:
-        # caller requested descending: restore the requested orientation.
-        tmp = a
-        a = b
-        b = tmp
-    return (a, b)
+    if lo == hi:
+        a = conditioned_lo(lo, hi)
+        b = conditioned_hi(lo, hi)
+        return (a, b)
+    return (lo, hi)
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # orientation-preserving case) or equal (the singular case that the
     # conditioning expands).
     Requires(lo > 0 and hi > 0 and lo < 1000000000000000 and hi < 1000000000000000)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # When the requested endpoints are distinct, the stored interval keeps the
@@ -117,15 +115,10 @@
     Ensures(Implies(lo == hi, Result()[0] < Result()[1]))
     # post-conditions-end
     # impl-start
-    swapped = lo > hi
     a = conditioned_lo(lo, hi)
     b = conditioned_hi(lo, hi)
-    # The conditioning normalises to strictly ascending order; the requested
-    # orientation, captured before conditioning, is restored afterwards.
-    if swapped:
-        # caller requested descending: restore the requested orientation.
-        tmp = a
-        a = b
-        b = tmp
+    tmp = a
+    a = b
+    b = tmp
     return (a, b)
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # orientation-preserving case) or equal (the singular case that the
     # conditioning expands).
     Requires(lo > 0 and hi > 0 and lo < 1000000000000000 and hi < 1000000000000000)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # When the requested endpoints are distinct, the stored interval keeps the
@@ -117,13 +115,10 @@
     Ensures(Implies(lo == hi, Result()[0] < Result()[1]))
     # post-conditions-end
     # impl-start
-    swapped = lo > hi
+    swapped = lo >= hi
     a = conditioned_lo(lo, hi)
     b = conditioned_hi(lo, hi)
-    # The conditioning normalises to strictly ascending order; the requested
-    # orientation, captured before conditioning, is restored afterwards.
     if swapped:
-        # caller requested descending: restore the requested orientation.
         tmp = a
         a = b
         b = tmp
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # orientation-preserving case) or equal (the singular case that the
     # conditioning expands).
     Requires(lo > 0 and hi > 0 and lo < 1000000000000000 and hi < 1000000000000000)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # When the requested endpoints are distinct, the stored interval keeps the
@@ -117,15 +115,5 @@
     Ensures(Implies(lo == hi, Result()[0] < Result()[1]))
     # post-conditions-end
     # impl-start
-    swapped = lo > hi
-    a = conditioned_lo(lo, hi)
-    b = conditioned_hi(lo, hi)
-    # The conditioning normalises to strictly ascending order; the requested
-    # orientation, captured before conditioning, is restored afterwards.
-    if swapped:
-        # caller requested descending: restore the requested orientation.
-        tmp = a
-        a = b
-        b = tmp
-    return (a, b)
+    return (lo, hi)
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # orientation-preserving case) or equal (the singular case that the
     # conditioning expands).
     Requires(lo > 0 and hi > 0 and lo < 1000000000000000 and hi < 1000000000000000)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # When the requested endpoints are distinct, the stored interval keeps the
@@ -117,15 +115,7 @@
     Ensures(Implies(lo == hi, Result()[0] < Result()[1]))
     # post-conditions-end
     # impl-start
-    swapped = lo > hi
-    a = conditioned_lo(lo, hi)
-    b = conditioned_hi(lo, hi)
-    # The conditioning normalises to strictly ascending order; the requested
-    # orientation, captured before conditioning, is restored afterwards.
-    if swapped:
-        # caller requested descending: restore the requested orientation.
-        tmp = a
-        a = b
-        b = tmp
-    return (a, b)
+    if lo == hi:
+        return (lo, hi + 1)
+    return (lo, hi)
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -31,7 +31,6 @@
 """
 from typing import Tuple
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -101,7 +100,6 @@
     # orientation-preserving case) or equal (the singular case that the
     # conditioning expands).
     Requires(lo > 0 and hi > 0 and lo < 1000000000000000 and hi < 1000000000000000)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # When the requested endpoints are distinct, the stored interval keeps the
@@ -117,15 +115,9 @@
     Ensures(Implies(lo == hi, Result()[0] < Result()[1]))
     # post-conditions-end
     # impl-start
-    swapped = lo > hi
     a = conditioned_lo(lo, hi)
     b = conditioned_hi(lo, hi)
-    # The conditioning normalises to strictly ascending order; the requested
-    # orientation, captured before conditioning, is restored afterwards.
-    if swapped:
-        # caller requested descending: restore the requested orientation.
-        tmp = a
-        a = b
-        b = tmp
+    if lo > hi:
+        return (b, a)
     return (a, b)
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-14623.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an axis view interval is set from a requested pair of endpoints, the
  stored interval must keep the orientation the caller requested. If the caller
  asks for a descending interval (first endpoint greater than the second), the
  stored interval must remain descending; if the caller asks for an ascending
  interval, it must remain ascending. This must hold uniformly, independently
  of the range-conditioning step that an axis may apply to its endpoints to
  avoid singular transforms and to clamp the range to the domain admissible for
  its scale -- a step which, for some scales, normalises the endpoints into
  ascending order. The conditioning may only adjust endpoint magnitudes; it may
  never decide the final orientation. The endpoint values themselves are
  preserved whenever the requested endpoints are distinct and already admissible
  for the scale.

The endpoints are modelled as `int` (the tested behaviour -- which of two
distinct admissible endpoints ends up first -- depends only on their order, not
on floating-point magnitude; refinement.md states the carrier correspondence).
The range-conditioning step (locator non-singular expansion followed by the
scale's domain clamp) is an UNCHANGED callee, axiomatised as `conditioned_lo` /
`conditioned_hi`: a pair-valued operation that always returns its two endpoints
in ascending order -- preserving the values when the endpoints are distinct, and
expanding the degenerate range into a strictly-ascending surrounding interval
when they are equal (the observable behaviour of a logarithmic axis'
conditioning). Its soundness against the real callees is checked out-of-band by
axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Tuple
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def conditioned_lo(lo: int, hi: int) -> int:
    """First component of the unchanged range-conditioning callee
    (locator non-singular expansion then the scale's domain clamp), applied to
    a requested endpoint pair of admissible (positive) endpoints.

    The conditioning ALWAYS normalises its output to ascending order and never
    decides the final orientation. For two DISTINCT endpoints it returns the
    smaller value, preserving the endpoint magnitudes. For two EQUAL endpoints
    it expands the degenerate range into a strictly-larger ascending interval;
    the only guaranteed fact about the first component there is that it ends up
    strictly below the (paired) second component -- the concrete expanded
    magnitude is scale-dependent and is NOT claimed.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    # The endpoints are admissible (positive) and lie in the magnitude range
    # over which the carrier is order-faithful and the conditioning preserves
    # distinct endpoint values exactly. Above this bound the non-singular
    # expansion fires on too-narrow relative gaps and the int->float carrier
    # loses distinctness; the tested inputs all sit well inside it (mapping.md
    # 2 / 3.1).
    Requires(lo > 0 and hi > 0 and lo < 1000000000000000 and hi < 1000000000000000)
    # Distinct endpoints: the smaller value is preserved exactly (min first).
    # Equal endpoints: no exact value is claimed -- the only consumed fact is
    # the cross-component ascending relation stated on conditioned_hi.
    Ensures(Implies(lo != hi, Result() == (lo if lo < hi else hi)))


@Pure
@ContractOnly
def conditioned_hi(lo: int, hi: int) -> int:
    """Second component of the unchanged range-conditioning callee. For two
    distinct admissible (positive) endpoints it returns the larger value; for
    two equal endpoints it returns the upper bound of the expanded ascending
    interval -- whose concrete magnitude is scale-dependent and NOT claimed.
    The only guaranteed (and only consumed) fact is the always-ascending
    relation: the second component is strictly greater than the first
    component for the same endpoint pair.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(lo > 0 and hi > 0 and lo < 1000000000000000 and hi < 1000000000000000)
    # Distinct endpoints: the larger value is preserved exactly (max second).
    Ensures(Implies(lo != hi, Result() == (hi if lo < hi else lo)))
    # Always-ascending: the conditioning returns its pair in ascending order
    # for EVERY admissible endpoint pair (distinct or equal). This is the
    # weakest fact the orientation proof consumes; no concrete equal-case
    # magnitude is asserted.
    Ensures(conditioned_lo(lo, hi) < Result())
# axioms-end


# pure-start
# (no pure helpers needed beyond the axiomatised conditioning callee)
# pure-end


def set_axis_interval(lo: int, hi: int) -> Tuple[int, int]:
    # pre-conditions-start
    # The endpoints reaching the conditioning step are admissible for the scale
    # (positive, as the log-domain validation upstream guarantees) and lie in
    # the order-faithful, value-preserving magnitude range (the tested inputs
    # are well inside it; mapping.md 2). They may be distinct (the
    # orientation-preserving case) or equal (the singular case that the
    # conditioning expands).
    Requires(lo > 0 and hi > 0 and lo < 1000000000000000 and hi < 1000000000000000)
    # pre-conditions-end
    # post-conditions-start
    # When the requested endpoints are distinct, the stored interval keeps the
    # requested orientation: a descending request stays descending, an ascending
    # request stays ascending -- regardless of how the conditioning step
    # reorders its output -- and the endpoint values are preserved exactly (the
    # conditioning does not expand an already-admissible non-degenerate range).
    Ensures(Implies(lo > hi, Result()[0] > Result()[1]))
    Ensures(Implies(lo < hi, Result()[0] < Result()[1]))
    Ensures(Implies(lo != hi, Result()[0] == lo and Result()[1] == hi))
    # When the requested endpoints are equal, the conditioning expands the
    # degenerate range, so the stored interval is strictly ascending.
    Ensures(Implies(lo == hi, Result()[0] < Result()[1]))
    # post-conditions-end
    # impl-start
    swapped = lo > hi
    a = conditioned_lo(lo, hi)
    b = conditioned_hi(lo, hi)
    # The conditioning normalises to strictly ascending order; the requested
    # orientation, captured before conditioning, is restored afterwards.
    if swapped:
        # caller requested descending: restore the requested orientation.
        tmp = a
        a = b
        b = tmp
    return (a, b)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

python=python; SBU_BENCHMARK_DIR=benchmark-verified; concurrent runs. Recorded gate state before this audit: G-EQ=fail INCONCLUSIVE (4 attacks inconclusive) — a Source-1 attack-verify-timeout artifact; positive control verifies in ~13s under calm load, so the prior INCONCLUSIVE was load-induced, not intrinsic.

### PROTOCOL RESULTS (7 same-spec attacks, spec bytes 1-116 byte-identical to model.py, confirmed via `adversary same-spec` for the candidates):
- atk_1 (prepatch bug: drop swapped-capture+restore, return conditioned ascending pair): `adversary weakness` => NOT-A-COUNTEREXAMPLE, verification FAILED (spec rejects). PREPATCH REPRODUCED (matches model_prepatch.py behavior; fails Implies(lo>hi, Result()[0]>Result()[1])).
- atk_3 (unconditional swap of conditioned pair): weakness => verification FAILED (distinct-ascending postcondition rejects). GOOD.
- atk_4 (boundary off-by-one: swapped = lo >= hi): weakness => verification FAILED (equal case becomes descending, violates Implies(lo==hi, Result()[0]<Result()[1])). GOOD.
- atk_5 (partial-domain: return (lo,hi) for all incl equal): weakness => verification FAILED (equal case not strictly ascending). GOOD.
- atk_2 (control-flow effect: BYPASS conditioning on distinct, apply it only when lo==hi): weakness => CANDIDATE (same-spec AND verifies, 15.3s). Faithful patch materialized (wrap conditioning in `if left==right:` at all 5 sites + ticker hunk) and RUN through official harness: RESOLVED=true, completed=true; FAIL_TO_PASS test_inverted_limits pass, all PASS_TO_PASS pass. NOT A BREAK — conditioning is a value-preserving no-op on tested distinct admissible endpoints.
- atk_6 (ungrounded/no-callee: never call conditioning; equal -> (v, v+1); distinct -> unchanged): weakness => CANDIDATE (verifies 13.6s). Faithful patch materialized (`if left==right: right = right + 1` at all 5 sites + ticker hunk) and RUN through harness: RESOLVED=true. NOT A BREAK — no test asserts the singular-expansion magnitude, and distinct inputs are already exact.
- atk_7 (restructured gold echo: condition then `if lo>hi: return (b,a)`): weakness => CANDIDATE (verifies 13.8s). Faithful patch is byte-identical to the gold patch; RUN through harness: RESOLVED=true. Expected echo control.

CONTROLS: gold patch (patch_gold.diff) RESOLVED=true (validates patch format + harness); positive_control.py (original model.py impl) VERIFIES (12.7s).

### Commands
  weakness:  python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-14623 <S>/atk_N.py
  same-spec: python -m swebench_unified.adversary same-spec nagini matplotlib__matplotlib-14623 <S>/atk_N.py
  verify:    bash scripts/nagini_verify.sh <S>/positive_control.py
  resolve:   swebench_unified.harness.run_resolve('matplotlib__matplotlib-14623', <patch_text>, timeout=1800) via <S>/resolve.py  (image swebench/sweb.eval.x86_64.matplotlib_1776_matplotlib-14623:latest pulled+retagged)
  base source extracted from image /testbed to <S>/repo for faithful diff construction.
  <S> = 

A-LEG / refinement.md AUDIT: refinement.md legs are all R/A-consumed/I (no kind-3): A1(R float<->int order-faithful), A2(I orientation compare), A3(A-consumed conditioning callee — weakest always-ascending + distinct value-preservation contract), A4(I temp swap), A5(R store<->return); §B1 A-consumed folds the ticker.py Locator.nonsingular coupled-prerequisite into the always-ascending axiom clause; §C confirms no axiomatization of the function-under-change. A-reference correspondence: axiom_check.py (G-AX=pass) exercises the REAL callees self.<ax>.get_major_locator().nonsingular(lo,hi) then limit_range_for_scale(lo,hi) on both log and linear scales against the literal model Ensures — matches mapping.md §3.1/§3.2. Correspondence holds.

VERDICT: SOUND. All 7 same-spec attacks were fully verified; the 3 that verify (atk_2, atk_6, atk_7) each had a faithful refined patch materialized and executed through the official harness, and ALL THREE RESOLVE. No verify-but-not-correct implementation exists. The spec's exact distinct-input postcondition makes verify => correct on the tested domain.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.py`, `atk_3.py`, `atk_4.py`, `atk_5.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_2.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verifying same-spec wrong impl produces a faithful patch that fails to resolve. The spec pins distinct-input output EXACTLY: Ensures(Implies(lo != hi, Result()[0] == lo and Result()[1] == hi)). Hence on every tested distinct pair (F2P: set_yscale('log'); set_ylim(10,1); expects (10,1); all P2P set_*lim calls use distinct admissible endpoints) any verifying impl coincides with the gold-patched code. The only behavioral freedom the spec leaves is (a) the equal/singular-endpoint expansion magnitude (spec requires only Result()[0] < Result()[1]) and (b) whether the conditioning callee is actually invoked on distinct admissible inputs (where nonsingular+limit_range_for_scale are value-preserving no-ops). Neither is observed by any FAIL_TO_PASS or PASS_TO_PASS assertion, so all three verifying candidates' faithful patches RESOLVE.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-14623.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When an axis view interval is set from a requested pair of endpoints, the
  stored interval must keep the orientation the caller requested. If the caller
  asks for a descending interval (first endpoint greater than the second), the
  stored interval must remain descending; if the caller asks for an ascending
  interval, it must remain ascending. This must hold uniformly, independently
  of the range-conditioning step that an axis may apply to its endpoints to
  avoid singular transforms and to clamp the range to the domain admissible for
  its scale -- a step which, for some scales, normalises the endpoints into
  ascending order. The conditioning may only adjust endpoint magnitudes; it may
  never decide the final orientation. The endpoint values themselves are
  preserved whenever the requested endpoints are distinct and already admissible
  for the scale.

The endpoints are modelled as `int` (the tested behaviour -- which of two
distinct admissible endpoints ends up first -- depends only on their order, not
on floating-point magnitude; refinement.md states the carrier correspondence).
The range-conditioning step (locator non-singular expansion followed by the
scale's domain clamp) is an UNCHANGED callee, axiomatised as `conditioned_lo` /
`conditioned_hi`: a pair-valued operation that always returns its two endpoints
in ascending order -- preserving the values when the endpoints are distinct, and
expanding the degenerate range into a strictly-ascending surrounding interval
when they are equal (the observable behaviour of a logarithmic axis'
conditioning). Its soundness against the real callees is checked out-of-band by
axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Tuple
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def conditioned_lo(lo: int, hi: int) -> int:
    """First component of the unchanged range-conditioning callee
    (locator non-singular expansion then the scale's domain clamp), applied to
    a requested endpoint pair of admissible (positive) endpoints.

    The conditioning ALWAYS normalises its output to ascending order and never
    decides the final orientation. For two DISTINCT endpoints it returns the
    smaller value, preserving the endpoint magnitudes. For two EQUAL endpoints
    it expands the degenerate range into a strictly-larger ascending interval;
    the only guaranteed fact about the first component there is that it ends up
    strictly below the (paired) second component -- the concrete expanded
    magnitude is scale-dependent and is NOT claimed.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    # The endpoints are admissible (positive) and lie in the magnitude range
    # over which the carrier is order-faithful and the conditioning preserves
    # distinct endpoint values exactly. Above this bound the non-singular
    # expansion fires on too-narrow relative gaps and the int->float carrier
    # loses distinctness; the tested inputs all sit well inside it (mapping.md
    # 2 / 3.1).
    Requires(lo > 0 and hi > 0 and lo < 1000000000000000 and hi < 1000000000000000)
    # Distinct endpoints: the smaller value is preserved exactly (min first).
    # Equal endpoints: no exact value is claimed -- the only consumed fact is
    # the cross-component ascending relation stated on conditioned_hi.
    Ensures(Implies(lo != hi, Result() == (lo if lo < hi else hi)))


@Pure
@ContractOnly
def conditioned_hi(lo: int, hi: int) -> int:
    """Second component of the unchanged range-conditioning callee. For two
    distinct admissible (positive) endpoints it returns the larger value; for
    two equal endpoints it returns the upper bound of the expanded ascending
    interval -- whose concrete magnitude is scale-dependent and NOT claimed.
    The only guaranteed (and only consumed) fact is the always-ascending
    relation: the second component is strictly greater than the first
    component for the same endpoint pair.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(lo > 0 and hi > 0 and lo < 1000000000000000 and hi < 1000000000000000)
    # Distinct endpoints: the larger value is preserved exactly (max second).
    Ensures(Implies(lo != hi, Result() == (hi if lo < hi else lo)))
    # Always-ascending: the conditioning returns its pair in ascending order
    # for EVERY admissible endpoint pair (distinct or equal). This is the
    # weakest fact the orientation proof consumes; no concrete equal-case
    # magnitude is asserted.
    Ensures(conditioned_lo(lo, hi) < Result())
# axioms-end


# pure-start
# (no pure helpers needed beyond the axiomatised conditioning callee)
# pure-end


def set_axis_interval(lo: int, hi: int) -> Tuple[int, int]:
    # pre-conditions-start
    # The endpoints reaching the conditioning step are admissible for the scale
    # (positive, as the log-domain validation upstream guarantees) and lie in
    # the order-faithful, value-preserving magnitude range (the tested inputs
    # are well inside it; mapping.md 2). They may be distinct (the
    # orientation-preserving case) or equal (the singular case that the
    # conditioning expands).
    Requires(lo > 0 and hi > 0 and lo < 1000000000000000 and hi < 1000000000000000)
    # pre-conditions-end
    # post-conditions-start
    # When the requested endpoints are distinct, the stored interval keeps the
    # requested orientation: a descending request stays descending, an ascending
    # request stays ascending -- regardless of how the conditioning step
    # reorders its output -- and the endpoint values are preserved exactly (the
    # conditioning does not expand an already-admissible non-degenerate range).
    Ensures(Implies(lo > hi, Result()[0] > Result()[1]))
    Ensures(Implies(lo < hi, Result()[0] < Result()[1]))
    Ensures(Implies(lo != hi, Result()[0] == lo and Result()[1] == hi))
    # When the requested endpoints are equal, the conditioning expands the
    # degenerate range, so the stored interval is strictly ascending.
    Ensures(Implies(lo == hi, Result()[0] < Result()[1]))
    # post-conditions-end
    # impl-start
    swapped = lo > hi
    a = conditioned_lo(lo, hi)
    b = conditioned_hi(lo, hi)
    # The conditioning normalises to strictly ascending order; the requested
    # orientation, captured before conditioning, is restored afterwards.
    if swapped:
        # caller requested descending: restore the requested orientation.
        tmp = a
        a = b
        b = tmp
    return (a, b)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

python=python; SBU_BENCHMARK_DIR=benchmark-verified; concurrent runs. Recorded gate state before this audit: G-EQ=fail INCONCLUSIVE (4 attacks inconclusive) — a Source-1 attack-verify-timeout artifact; positive control verifies in ~13s under calm load, so the prior INCONCLUSIVE was load-induced, not intrinsic.

### PROTOCOL RESULTS (7 same-spec attacks, spec bytes 1-116 byte-identical to model.py, confirmed via `adversary same-spec` for the candidates):
- atk_1 (prepatch bug: drop swapped-capture+restore, return conditioned ascending pair): `adversary weakness` => NOT-A-COUNTEREXAMPLE, verification FAILED (spec rejects). PREPATCH REPRODUCED (matches model_prepatch.py behavior; fails Implies(lo>hi, Result()[0]>Result()[1])).
- atk_3 (unconditional swap of conditioned pair): weakness => verification FAILED (distinct-ascending postcondition rejects). GOOD.
- atk_4 (boundary off-by-one: swapped = lo >= hi): weakness => verification FAILED (equal case becomes descending, violates Implies(lo==hi, Result()[0]<Result()[1])). GOOD.
- atk_5 (partial-domain: return (lo,hi) for all incl equal): weakness => verification FAILED (equal case not strictly ascending). GOOD.
- atk_2 (control-flow effect: BYPASS conditioning on distinct, apply it only when lo==hi): weakness => CANDIDATE (same-spec AND verifies, 15.3s). Faithful patch materialized (wrap conditioning in `if left==right:` at all 5 sites + ticker hunk) and RUN through official harness: RESOLVED=true, completed=true; FAIL_TO_PASS test_inverted_limits pass, all PASS_TO_PASS pass. NOT A BREAK — conditioning is a value-preserving no-op on tested distinct admissible endpoints.
- atk_6 (ungrounded/no-callee: never call conditioning; equal -> (v, v+1); distinct -> unchanged): weakness => CANDIDATE (verifies 13.6s). Faithful patch materialized (`if left==right: right = right + 1` at all 5 sites + ticker hunk) and RUN through harness: RESOLVED=true. NOT A BREAK — no test asserts the singular-expansion magnitude, and distinct inputs are already exact.
- atk_7 (restructured gold echo: condition then `if lo>hi: return (b,a)`): weakness => CANDIDATE (verifies 13.8s). Faithful patch is byte-identical to the gold patch; RUN through harness: RESOLVED=true. Expected echo control.

CONTROLS: gold patch (patch_gold.diff) RESOLVED=true (validates patch format + harness); positive_control.py (original model.py impl) VERIFIES (12.7s).

### Commands
  weakness:  python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-14623 <S>/atk_N.py
  same-spec: python -m swebench_unified.adversary same-spec nagini matplotlib__matplotlib-14623 <S>/atk_N.py
  verify:    bash scripts/nagini_verify.sh <S>/positive_control.py
  resolve:   swebench_unified.harness.run_resolve('matplotlib__matplotlib-14623', <patch_text>, timeout=1800) via <S>/resolve.py  (image swebench/sweb.eval.x86_64.matplotlib_1776_matplotlib-14623:latest pulled+retagged)
  base source extracted from image /testbed to <S>/repo for faithful diff construction.
  <S> = 

A-LEG / refinement.md AUDIT: refinement.md legs are all R/A-consumed/I (no kind-3): A1(R float<->int order-faithful), A2(I orientation compare), A3(A-consumed conditioning callee — weakest always-ascending + distinct value-preservation contract), A4(I temp swap), A5(R store<->return); §B1 A-consumed folds the ticker.py Locator.nonsingular coupled-prerequisite into the always-ascending axiom clause; §C confirms no axiomatization of the function-under-change. A-reference correspondence: axiom_check.py (G-AX=pass) exercises the REAL callees self.<ax>.get_major_locator().nonsingular(lo,hi) then limit_range_for_scale(lo,hi) on both log and linear scales against the literal model Ensures — matches mapping.md §3.1/§3.2. Correspondence holds.

VERDICT: SOUND. All 7 same-spec attacks were fully verified; the 3 that verify (atk_2, atk_6, atk_7) each had a faithful refined patch materialized and executed through the official harness, and ALL THREE RESOLVE. No verify-but-not-correct implementation exists. The spec's exact distinct-input postcondition makes verify => correct on the tested domain.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check on matplotlib__matplotlib-14623 nagini bundle. The only modeling boundary is the @ContractOnly axiom pair conditioned_lo/conditioned_hi standing in for the real conditioning callee (get_major_locator().nonsingular(lo,hi) then limit_range_for_scale(...)). Requires domain: lo>0, hi>0, lo<1e15, hi<1e15. Axiom Ensures: (a) always-ascending conditioned_lo<conditioned_hi; (b) distinct endpoints -> exact min/max value-preservation; (c) equal endpoints -> only ascending (no magnitude claimed).

Checked against REAL matplotlib callee: (1) distinct value-preservation is analytically sound -- mtransforms.nonsingular expands only when gap <= maxabsvalue*1e-15; in-domain maxabsvalue<1e15 => expansion threshold <1.0, while distinct ints have gap>=1, so no expansion fires in-domain, and both LogLocator and the post-patch base Locator sort ascending. Empirically 0 mismatches over ~8000 pairs (boundary + fuzz over full [1,1e15) range) on log and linear. (2) equal-case: real callee always expands to strictly-ascending; axiom claims only ascending -- holds, and correctly does NOT claim the old over-specified lo-1/hi+1. (3) end-to-end gold-patched set_ylim matches all four model postconditions on ~4000 inputs.

Spec region byte-identical (same-spec command exit 0). Model verifies in Nagini (12.7s). model_prepatch drops swapped-restore and fails the orientation postcondition (G-DIFF sensitivity intact). The 1e15 Requires bound is load-bearing and correct, not artificially narrowing. No input in the Requires domain where the modeled function disagrees with the real callee. Spec is not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen on the actual spec_view -> passed=True, zero hard failures) and independent semantic review confirms NO-LEAKAGE.

Public problem_statement already discloses the full desired behavior: 'Inverting an axis using its limits does not work for log scale ... I would expect the yaxis to be inverted for both the linear and the log scale.' i.e. set_ylim(hi, lo) with hi>lo must keep the requested descending orientation for the log scale too.

Spec-view assessed line by line:
- Postconditions on set_axis_interval (Implies(lo>hi, Result()[0]>Result()[1]); ascending-stays-ascending; distinct value-preservation; equal->ascending) restate exactly the publicly-requested orientation-preservation — the WHAT, already public via the task. Not the edit.
- Axiom docstrings/comments (conditioned_lo/conditioned_hi) describe the UNCHANGED conditioning callee ('always normalises output to ascending order and never decides the final orientation'). That is matplotlib-internal callee behavior, not the patch's discriminating change.
- The gold mechanism is HIDDEN: the discriminating edit (swapped = left>right capture + 'if swapped: right,left' restore at the five set_*lim* sites, plus the ticker.py increasing=False drop) lives entirely in the impl region, which is elided in the spec view ('... implementation elided — supplied by the consumer'). The solver never sees it.

Lexical confirmation (all clean): no gold-diff line reproduced (>=8 chars normalized), no diff markers, no patched file path (lib/matplotlib/axes/_base.py, lib/matplotlib/ticker.py, lib/mpl_toolkits/mplot3d/axes3d.py all absent), no patched repo symbol (set_xlim/set_ylim/set_*lim3d/nonsingular/increasing/swapped) embedded in spec-view identifiers or comments, no bug/fix narration. relaxed_leakage flag not set; recorded G-LEAK status 'pass'.

refinement.md / mapping.md / axiom_check.py are auditor-only artifacts, not part of the solver-visible spec view, so their gold-mechanism prose is out of scope for G-PANEL-3. The spec view leaks nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
