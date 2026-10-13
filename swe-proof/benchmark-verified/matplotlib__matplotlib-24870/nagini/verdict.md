# P2 adversarial audit — matplotlib__matplotlib-24870

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `model.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -104,7 +103,6 @@
     # (its distance below the upper value equals its distance above the lower
     # value). This linear defining equation grounds `mid` in the data extents.
     Requires(mid - zmin == zmax - mid)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -133,14 +131,6 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[float]
-    if two_valued:
-        # `mid` is equidistant from the two distinct values, so it lies strictly
-        # between them: zmin < mid < zmax.
-        if filled:
-            result = [zmin, mid, zmax]
-        else:
-            result = [mid]
-    else:
-        result = list(auto_levels(zmin, zmax))
+    result = list(auto_levels(zmin, zmax))
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -104,7 +103,6 @@
     # (its distance below the upper value equals its distance above the lower
     # value). This linear defining equation grounds `mid` in the data extents.
     Requires(mid - zmin == zmax - mid)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -134,12 +132,7 @@
     # impl-start
     result = []  # type: List[float]
     if two_valued:
-        # `mid` is equidistant from the two distinct values, so it lies strictly
-        # between them: zmin < mid < zmax.
-        if filled:
-            result = [zmin, mid, zmax]
-        else:
-            result = [mid]
+        result = [mid]
     else:
         result = list(auto_levels(zmin, zmax))
     return result
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -104,7 +103,6 @@
     # (its distance below the upper value equals its distance above the lower
     # value). This linear defining equation grounds `mid` in the data extents.
     Requires(mid - zmin == zmax - mid)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -134,10 +132,8 @@
     # impl-start
     result = []  # type: List[float]
     if two_valued:
-        # `mid` is equidistant from the two distinct values, so it lies strictly
-        # between them: zmin < mid < zmax.
         if filled:
-            result = [zmin, mid, zmax]
+            result = [zmin, mid, mid, zmax]
         else:
             result = [mid]
     else:
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -104,7 +103,6 @@
     # (its distance below the upper value equals its distance above the lower
     # value). This linear defining equation grounds `mid` in the data extents.
     Requires(mid - zmin == zmax - mid)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -134,10 +132,8 @@
     # impl-start
     result = []  # type: List[float]
     if two_valued:
-        # `mid` is equidistant from the two distinct values, so it lies strictly
-        # between them: zmin < mid < zmax.
         if filled:
-            result = [zmin, mid, zmax]
+            result = [zmax, mid, zmin]
         else:
             result = [mid]
     else:
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -104,7 +103,6 @@
     # (its distance below the upper value equals its distance above the lower
     # value). This linear defining equation grounds `mid` in the data extents.
     Requires(mid - zmin == zmax - mid)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -134,12 +132,10 @@
     # impl-start
     result = []  # type: List[float]
     if two_valued:
-        # `mid` is equidistant from the two distinct values, so it lies strictly
-        # between them: zmin < mid < zmax.
         if filled:
             result = [zmin, mid, zmax]
         else:
-            result = [mid]
+            result = [zmin]
     else:
         result = list(auto_levels(zmin, zmax))
     return result
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -104,7 +103,6 @@
     # (its distance below the upper value equals its distance above the lower
     # value). This linear defining equation grounds `mid` in the data extents.
     Requires(mid - zmin == zmax - mid)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -134,13 +132,11 @@
     # impl-start
     result = []  # type: List[float]
     if two_valued:
-        # `mid` is equidistant from the two distinct values, so it lies strictly
-        # between them: zmin < mid < zmax.
         if filled:
             result = [zmin, mid, zmax]
         else:
             result = [mid]
     else:
-        result = list(auto_levels(zmin, zmax))
+        result = [zmin, zmax]
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -44,7 +44,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -104,7 +103,6 @@
     # (its distance below the upper value equals its distance above the lower
     # value). This linear defining equation grounds `mid` in the data extents.
     Requires(mid - zmin == zmax - mid)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -133,14 +131,11 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[float]
-    if two_valued:
-        # `mid` is equidistant from the two distinct values, so it lies strictly
-        # between them: zmin < mid < zmax.
-        if filled:
-            result = [zmin, mid, zmax]
-        else:
-            result = [mid]
+    if not two_valued:
+        result = list(auto_levels(zmin, zmax))
+    elif filled:
+        result = [zmin, mid, zmax]
     else:
-        result = list(auto_levels(zmin, zmax))
+        result = [mid]
     return result
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -104,7 +103,6 @@
     # (its distance below the upper value equals its distance above the lower
     # value). This linear defining equation grounds `mid` in the data extents.
     Requires(mid - zmin == zmax - mid)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -134,12 +132,10 @@
     # impl-start
     result = []  # type: List[float]
     if two_valued:
-        # `mid` is equidistant from the two distinct values, so it lies strictly
-        # between them: zmin < mid < zmax.
         if filled:
             result = [zmin, mid, zmax]
         else:
-            result = [mid]
+            result = [mid, mid]
     else:
         result = list(auto_levels(zmin, zmax))
     return result
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `model.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-24870.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A contour routine must choose a default set of contour levels when the caller
  supplies neither an explicit level list nor an explicit level count. The data
  field being contoured has a known minimum and maximum value (`zmin`, `zmax`,
  with `zmin < zmax`) and is one of two kinds:

    * a two-valued field, whose every sample is one of exactly two distinct
      values (the lower value `zmin` and the upper value `zmax`); or
    * an ordinary continuous field.

  For an ordinary continuous field the default is the long-standing automatic
  selection that spreads several (more than one) interior levels across the data
  range. That choice is useless for a two-valued field: the only meaningful
  place to draw a boundary between the two regions is a single level strictly
  between the two values. So for a two-valued field the default levels MUST be:

    * for a line contour:  a single level, the midpoint of the two values (the
      value equidistant from both), which therefore lies strictly between them
      (so it survives the line-contour rule that drops any level not strictly
      inside the open data range);
    * for a filled contour: the three levels  [zmin, midpoint, zmax]  — the two
      extreme values bracketing the midpoint — which is a valid filled
      specification (a filled contour requires at least two levels).

  The choice depends only on (a) whether explicit levels were requested, (b)
  whether the field is two-valued, and (c) whether the contour is filled; it
  must NOT collapse the two-valued field onto the ordinary multi-level default.

The data extents and the chosen levels are interpreted real numbers (verified
with `--float-encoding=real`) because the behaviour at stake — a single level
lying strictly between the two values, equidistant from each — is a real-valued
relation the tests probe to floating tolerance. The midpoint enters pinned by
its linear defining equation (it is equidistant from the two values), which both
grounds it in the data extents and stays inside the verifier's linear real
fragment. The ordinary multi-level automatic selection (the unchanged path for
continuous fields) is the operation this routine delegates to; it is axiomatized
with the weakest sufficient contract (it yields more than one level) and
validated against the real selection out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def auto_levels(zmin: float, zmax: float) -> PSeq[float]:
    """The ordinary automatic level selection for a continuous field (the
    unchanged delegate). Across a well-resolved data range it produces more
    than one level — so a two-valued field, where a single boundary level is
    wanted, needs its own default rather than this multi-level spread. The
    weakest contract the proof needs (more than one level).

    The "more than one level" guarantee holds only when the data range is
    well-resolved: the span must clear an absolute floor AND a small fraction
    of each extent's magnitude. At an unresolvable range — a span at or below
    the floating-point spacing near the extents, or extents at the underflow
    floor — the automatic selection degenerates to a single tick, so the
    obligation is scoped (via Requires) to the resolved regime, which is the
    only regime the operation under specification is ever applied to (the
    tested two-valued range [0, 1] clears it with enormous margin). Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(zmin < zmax)
    # Well-resolved range: span clears an absolute floor and a small fraction of
    # each extent's magnitude. (Outside this the real selection can collapse to
    # a single tick; the proof never needs the multi-level fact there.)
    Requires(zmax - zmin >= 1e-6)
    Requires(zmax - zmin >= 1e-9 * zmax)
    Requires(zmax - zmin >= 1e-9 * (0.0 - zmin))
    Ensures(len(Result()) > 1)
# axioms-end

# pure-start
# (no pure helpers — the midpoint is pinned by its linear defining equation in
# the precondition, see `mid` below.)
# pure-end

def choose_default_levels(has_explicit: bool, two_valued: bool, filled: bool,
                          zmin: float, zmax: float, mid: float) -> List[float]:
    # pre-conditions-start
    # The branch under specification is the no-explicit-levels default; the data
    # range is non-degenerate (the two values differ).
    Requires(not has_explicit)
    Requires(zmin < zmax)
    # Well-resolved data range: the span clears an absolute floor and a small
    # fraction of each extent's magnitude. This excludes only an unresolvable
    # range (a span at or below the floating-point spacing near the extents, or
    # extents at the underflow floor), where the ordinary automatic selection
    # would degenerate to a single tick. Every meaningful contour range — in
    # particular the tested two-valued range [0, 1] — clears it with margin.
    Requires(zmax - zmin >= 1e-6)
    Requires(zmax - zmin >= 1e-9 * zmax)
    Requires(zmax - zmin >= 1e-9 * (0.0 - zmin))
    # `mid` is the midpoint of the two values: the value equidistant from each
    # (its distance below the upper value equals its distance above the lower
    # value). This linear defining equation grounds `mid` in the data extents.
    Requires(mid - zmin == zmax - mid)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # A two-valued field gets the boundary-level default, NOT the ordinary
    # multi-level automatic selection.
    # Line contour over a two-valued field: exactly one level, the midpoint of
    # the two values, lying strictly between them.
    Ensures(Implies(two_valued and not filled, len(Result()) == 1))
    Ensures(Implies(two_valued and not filled, Result()[0] == mid))
    Ensures(Implies(two_valued and not filled,
                    zmin < Result()[0] and Result()[0] < zmax))
    # Filled contour over a two-valued field: the three levels
    # [zmin, midpoint, zmax] — at least two levels, the extremes bracketing the
    # strictly-interior midpoint.
    Ensures(Implies(two_valued and filled, len(Result()) == 3))
    Ensures(Implies(two_valued and filled, len(Result()) >= 2))
    Ensures(Implies(two_valued and filled,
                    Result()[0] == zmin and Result()[2] == zmax))
    Ensures(Implies(two_valued and filled, Result()[1] == mid))
    Ensures(Implies(two_valued and filled,
                    Result()[0] < Result()[1] and Result()[1] < Result()[2]))
    # An ordinary continuous field keeps the unchanged multi-level default
    # (more than one level), so the two regimes are not conflated.
    Ensures(Implies(not two_valued, len(Result()) > 1))
    Ensures(Implies(not two_valued, ToSeq(Result()) == auto_levels(zmin, zmax)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[float]
    if two_valued:
        # `mid` is equidistant from the two distinct values, so it lies strictly
        # between them: zmin < mid < zmax.
        if filled:
            result = [zmin, mid, zmax]
        else:
            result = [mid]
    else:
        result = list(auto_levels(zmin, zmax))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. verify => correct holds for this bundle; no verifying same-spec wrong impl was found whose faithful patch fails to resolve.

### Positive control
`python -m swebench_unified.adversary verify nagini matplotlib__matplotlib-24870 <model.py>` => VERIFIED in 20.8s (exit 0). Original model.py verifies.

### Prepatch reproduced
atk_1.py IS the model_prepatch impl (no-explicit -> always list(auto_levels)). `adversary weakness` => NOT-A-COUNTEREXAMPLE (does not verify), i.e. the spec REJECTS the prepatch bug (G-DIFF sensitivity intact). prepatch_reproduced=true.

### 8 same-spec attacks (all same-spec exit 0; only impl region edited byte-for-byte)
Command each: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-24870 atk_N.py`
- atk_1 (prepatch: always auto_levels)              -> NOT-A-COUNTEREXAMPLE (does not verify)
- atk_2 (control-flow: ignores `filled`, two_valued -> [mid] always) -> does not verify
- atk_3 (boundary: filled two_valued -> [zmin,mid,mid,zmax], len 4) -> does not verify
- atk_4 (swap/order: filled two_valued -> [zmax,mid,zmin] descending) -> does not verify
- atk_5 (partial-domain: line two_valued -> [zmin], not interior mid) -> does not verify
- atk_6 (ungrounded continuous: not two_valued -> [zmin,zmax] instead of auto_levels) -> does not verify
- atk_7 (gold-behaviour echo: branches reordered, semantics identical to gold) -> CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 16.3s, exit 0)
- atk_8 (boundary: line two_valued -> [mid,mid], len 2) -> does not verify
Run concurrently in batches of <=3 background jobs (each Nagini check = 1 JVM+Z3).

### Resolve of the ONLY verifying candidate (atk_7)
atk_7 is behaviourally identical to gold in every reachable branch, because the spec pins Result() EXACTLY: line-two_valued=>[mid]; filled-two_valued=>[zmin,mid,zmax] strictly increasing with [0]==zmin,[2]==zmax; not-two_valued=>ToSeq(Result())==auto_levels(zmin,zmax). Its faithful refined patch is therefore the gold patch verbatim (see patches[atk_7]). This is INCONCLUSIVE-shaped from the wrapper, NOT a real non-resolve.

I therefore ran the official harness DIRECTLY: cd .../experiments && python -m swebench_unified.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified --predictions_path <preds> --max_workers 1 --run_id sbu-eqaudit-ntvn-diag --namespace swebench --instance_image_tag latest --cache_level env ----report_dir .../reports --instance_ids matplotlib__matplotlib-24870 Result (report.json at .../run_evaluation/sbu-eqaudit-ntvn-diag/sbu_patch/matplotlib__matplotlib-24870/report.json): patch_successfully_applied=true, resolved=TRUE, FAIL_TO_PASS success=[test_bool_autolevel] failure=[], PASS_TO_PASS failure=[] (all 65 pass). Evaluation bar: 1 instance, checkmark=1, cross=0, error=0. => The one verifying candidate RESOLVES. Under the 2026-08-06 G-PANEL-1/G-EQ policy a resolving same-spec echo of gold is NOT a weakness. verify => correct is preserved. Nothing breaks the spec.

### refinement.md A-leg audit
Leg kinds: A1=R/I, A2=R, A3=I, A4=R, A5=R, A6=A-consumed, B1/B2=R. NO kind-3 (unexpressible-changed-op) legs -- the operation that genuinely changed (the two-valued default level selection) is modeled DIRECTLY in the impl (`two_valued` branches producing [mid] / [zmin,mid,zmax]), not hidden behind an axiom. Only consumed axiom = auto_levels (A6, A-consumed): abstracts the UNCHANGED continuous-field delegate levels_arg=7 -> _autolev(7) -> MaxNLocator(N+1).tick_values trimmed. The gold diff LEAVES the `else: levels_arg=7` branch intact, so the callee is genuinely unchanged -- correspondence holds.

Proof consumes only len(auto_levels)>1, scoped to a WELL-RESOLVED range (span>=1e-6, >=1e-9*zmax, >=1e-9*(-zmin)); the tested bool range [0,1] clears the guard with huge margin, so the discriminating two-valued behaviour is untouched by the scoping. axiom_check.py (G-AX, A-reference validation) drives the REAL matplotlib default selection (plt.contour on continuous fields) over boundary + 2000 randomized well-resolved ranges asserting len>1, and confirms the documented collapse witnesses ((1e-300,2e-300)->[1e-300] etc.) are exactly the guard-EXCLUDED regime -- so the axiom does not over-claim. meta records G-AX and G-RESOLVE(gold)=resolved.

Model<->patch correspondence for the changed op is confirmed empirically: the 7 divergent same-spec impls are all rejected by the spec, and the single verifying same-spec impl resolves -- consistent with the postconditions pinning Result() exactly in every reachable branch.

CONCLUSION: >=8 attacks run and reported; prepatch reproduced; positive control verifies; the sole verifying candidate's faithful patch RESOLVES (executed, report.json resolved=true). No verify-but-not-resolve witness exists. Refinement legs are all R/A-consumed/A-reference/I with sound A-leg correspondence. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `model.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `model.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-24870.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A contour routine must choose a default set of contour levels when the caller
  supplies neither an explicit level list nor an explicit level count. The data
  field being contoured has a known minimum and maximum value (`zmin`, `zmax`,
  with `zmin < zmax`) and is one of two kinds:

    * a two-valued field, whose every sample is one of exactly two distinct
      values (the lower value `zmin` and the upper value `zmax`); or
    * an ordinary continuous field.

  For an ordinary continuous field the default is the long-standing automatic
  selection that spreads several (more than one) interior levels across the data
  range. That choice is useless for a two-valued field: the only meaningful
  place to draw a boundary between the two regions is a single level strictly
  between the two values. So for a two-valued field the default levels MUST be:

    * for a line contour:  a single level, the midpoint of the two values (the
      value equidistant from both), which therefore lies strictly between them
      (so it survives the line-contour rule that drops any level not strictly
      inside the open data range);
    * for a filled contour: the three levels  [zmin, midpoint, zmax]  — the two
      extreme values bracketing the midpoint — which is a valid filled
      specification (a filled contour requires at least two levels).

  The choice depends only on (a) whether explicit levels were requested, (b)
  whether the field is two-valued, and (c) whether the contour is filled; it
  must NOT collapse the two-valued field onto the ordinary multi-level default.

The data extents and the chosen levels are interpreted real numbers (verified
with `--float-encoding=real`) because the behaviour at stake — a single level
lying strictly between the two values, equidistant from each — is a real-valued
relation the tests probe to floating tolerance. The midpoint enters pinned by
its linear defining equation (it is equidistant from the two values), which both
grounds it in the data extents and stays inside the verifier's linear real
fragment. The ordinary multi-level automatic selection (the unchanged path for
continuous fields) is the operation this routine delegates to; it is axiomatized
with the weakest sufficient contract (it yields more than one level) and
validated against the real selection out-of-band by axiom_check.py (G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def auto_levels(zmin: float, zmax: float) -> PSeq[float]:
    """The ordinary automatic level selection for a continuous field (the
    unchanged delegate). Across a well-resolved data range it produces more
    than one level — so a two-valued field, where a single boundary level is
    wanted, needs its own default rather than this multi-level spread. The
    weakest contract the proof needs (more than one level).

    The "more than one level" guarantee holds only when the data range is
    well-resolved: the span must clear an absolute floor AND a small fraction
    of each extent's magnitude. At an unresolvable range — a span at or below
    the floating-point spacing near the extents, or extents at the underflow
    floor — the automatic selection degenerates to a single tick, so the
    obligation is scoped (via Requires) to the resolved regime, which is the
    only regime the operation under specification is ever applied to (the
    tested two-valued range [0, 1] clears it with enormous margin). Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(zmin < zmax)
    # Well-resolved range: span clears an absolute floor and a small fraction of
    # each extent's magnitude. (Outside this the real selection can collapse to
    # a single tick; the proof never needs the multi-level fact there.)
    Requires(zmax - zmin >= 1e-6)
    Requires(zmax - zmin >= 1e-9 * zmax)
    Requires(zmax - zmin >= 1e-9 * (0.0 - zmin))
    Ensures(len(Result()) > 1)
# axioms-end

# pure-start
# (no pure helpers — the midpoint is pinned by its linear defining equation in
# the precondition, see `mid` below.)
# pure-end

def choose_default_levels(has_explicit: bool, two_valued: bool, filled: bool,
                          zmin: float, zmax: float, mid: float) -> List[float]:
    # pre-conditions-start
    # The branch under specification is the no-explicit-levels default; the data
    # range is non-degenerate (the two values differ).
    Requires(not has_explicit)
    Requires(zmin < zmax)
    # Well-resolved data range: the span clears an absolute floor and a small
    # fraction of each extent's magnitude. This excludes only an unresolvable
    # range (a span at or below the floating-point spacing near the extents, or
    # extents at the underflow floor), where the ordinary automatic selection
    # would degenerate to a single tick. Every meaningful contour range — in
    # particular the tested two-valued range [0, 1] — clears it with margin.
    Requires(zmax - zmin >= 1e-6)
    Requires(zmax - zmin >= 1e-9 * zmax)
    Requires(zmax - zmin >= 1e-9 * (0.0 - zmin))
    # `mid` is the midpoint of the two values: the value equidistant from each
    # (its distance below the upper value equals its distance above the lower
    # value). This linear defining equation grounds `mid` in the data extents.
    Requires(mid - zmin == zmax - mid)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # A two-valued field gets the boundary-level default, NOT the ordinary
    # multi-level automatic selection.
    # Line contour over a two-valued field: exactly one level, the midpoint of
    # the two values, lying strictly between them.
    Ensures(Implies(two_valued and not filled, len(Result()) == 1))
    Ensures(Implies(two_valued and not filled, Result()[0] == mid))
    Ensures(Implies(two_valued and not filled,
                    zmin < Result()[0] and Result()[0] < zmax))
    # Filled contour over a two-valued field: the three levels
    # [zmin, midpoint, zmax] — at least two levels, the extremes bracketing the
    # strictly-interior midpoint.
    Ensures(Implies(two_valued and filled, len(Result()) == 3))
    Ensures(Implies(two_valued and filled, len(Result()) >= 2))
    Ensures(Implies(two_valued and filled,
                    Result()[0] == zmin and Result()[2] == zmax))
    Ensures(Implies(two_valued and filled, Result()[1] == mid))
    Ensures(Implies(two_valued and filled,
                    Result()[0] < Result()[1] and Result()[1] < Result()[2]))
    # An ordinary continuous field keeps the unchanged multi-level default
    # (more than one level), so the two regimes are not conflated.
    Ensures(Implies(not two_valued, len(Result()) > 1))
    Ensures(Implies(not two_valued, ToSeq(Result()) == auto_levels(zmin, zmax)))
    # post-conditions-end
    # impl-start
    result = []  # type: List[float]
    if two_valued:
        # `mid` is equidistant from the two distinct values, so it lies strictly
        # between them: zmin < mid < zmax.
        if filled:
            result = [zmin, mid, zmax]
        else:
            result = [mid]
    else:
        result = list(auto_levels(zmin, zmax))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. verify => correct holds for this bundle; no verifying same-spec wrong impl was found whose faithful patch fails to resolve.

### Positive control
`python -m swebench_unified.adversary verify nagini matplotlib__matplotlib-24870 <model.py>` => VERIFIED in 20.8s (exit 0). Original model.py verifies.

### Prepatch reproduced
atk_1.py IS the model_prepatch impl (no-explicit -> always list(auto_levels)). `adversary weakness` => NOT-A-COUNTEREXAMPLE (does not verify), i.e. the spec REJECTS the prepatch bug (G-DIFF sensitivity intact). prepatch_reproduced=true.

### 8 same-spec attacks (all same-spec exit 0; only impl region edited byte-for-byte)
Command each: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-24870 atk_N.py`
- atk_1 (prepatch: always auto_levels)              -> NOT-A-COUNTEREXAMPLE (does not verify)
- atk_2 (control-flow: ignores `filled`, two_valued -> [mid] always) -> does not verify
- atk_3 (boundary: filled two_valued -> [zmin,mid,mid,zmax], len 4) -> does not verify
- atk_4 (swap/order: filled two_valued -> [zmax,mid,zmin] descending) -> does not verify
- atk_5 (partial-domain: line two_valued -> [zmin], not interior mid) -> does not verify
- atk_6 (ungrounded continuous: not two_valued -> [zmin,zmax] instead of auto_levels) -> does not verify
- atk_7 (gold-behaviour echo: branches reordered, semantics identical to gold) -> CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 16.3s, exit 0)
- atk_8 (boundary: line two_valued -> [mid,mid], len 2) -> does not verify
Run concurrently in batches of <=3 background jobs (each Nagini check = 1 JVM+Z3).

### Resolve of the ONLY verifying candidate (atk_7)
atk_7 is behaviourally identical to gold in every reachable branch, because the spec pins Result() EXACTLY: line-two_valued=>[mid]; filled-two_valued=>[zmin,mid,zmax] strictly increasing with [0]==zmin,[2]==zmax; not-two_valued=>ToSeq(Result())==auto_levels(zmin,zmax). Its faithful refined patch is therefore the gold patch verbatim (see patches[atk_7]). This is INCONCLUSIVE-shaped from the wrapper, NOT a real non-resolve.

I therefore ran the official harness DIRECTLY: cd .../experiments && python -m swebench_unified.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified --predictions_path <preds> --max_workers 1 --run_id sbu-eqaudit-ntvn-diag --namespace swebench --instance_image_tag latest --cache_level env ----report_dir .../reports --instance_ids matplotlib__matplotlib-24870 Result (report.json at .../run_evaluation/sbu-eqaudit-ntvn-diag/sbu_patch/matplotlib__matplotlib-24870/report.json): patch_successfully_applied=true, resolved=TRUE, FAIL_TO_PASS success=[test_bool_autolevel] failure=[], PASS_TO_PASS failure=[] (all 65 pass). Evaluation bar: 1 instance, checkmark=1, cross=0, error=0. => The one verifying candidate RESOLVES. Under the 2026-08-06 G-PANEL-1/G-EQ policy a resolving same-spec echo of gold is NOT a weakness. verify => correct is preserved. Nothing breaks the spec.

### refinement.md A-leg audit
Leg kinds: A1=R/I, A2=R, A3=I, A4=R, A5=R, A6=A-consumed, B1/B2=R. NO kind-3 (unexpressible-changed-op) legs -- the operation that genuinely changed (the two-valued default level selection) is modeled DIRECTLY in the impl (`two_valued` branches producing [mid] / [zmin,mid,zmax]), not hidden behind an axiom. Only consumed axiom = auto_levels (A6, A-consumed): abstracts the UNCHANGED continuous-field delegate levels_arg=7 -> _autolev(7) -> MaxNLocator(N+1).tick_values trimmed. The gold diff LEAVES the `else: levels_arg=7` branch intact, so the callee is genuinely unchanged -- correspondence holds.

Proof consumes only len(auto_levels)>1, scoped to a WELL-RESOLVED range (span>=1e-6, >=1e-9*zmax, >=1e-9*(-zmin)); the tested bool range [0,1] clears the guard with huge margin, so the discriminating two-valued behaviour is untouched by the scoping. axiom_check.py (G-AX, A-reference validation) drives the REAL matplotlib default selection (plt.contour on continuous fields) over boundary + 2000 randomized well-resolved ranges asserting len>1, and confirms the documented collapse witnesses ((1e-300,2e-300)->[1e-300] etc.) are exactly the guard-EXCLUDED regime -- so the axiom does not over-claim. meta records G-AX and G-RESOLVE(gold)=resolved.

Model<->patch correspondence for the changed op is confirmed empirically: the 7 divergent same-spec impls are all rejected by the spec, and the single verifying same-spec impl resolves -- consistent with the postconditions pinning Result() exactly in every reachable branch.

CONCLUSION: >=8 attacks run and reported; prepatch reproduced; positive control verifies; the sole verifying candidate's faithful patch RESOLVES (executed, report.json resolved=true). No verify-but-not-resolve witness exists. Refinement legs are all R/A-consumed/A-reference/I with sound A-leg correspondence. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of the modeled function choose_default_levels vs the real callee ContourSet._process_contour_level_args (self.levels is None default-selection block, lib/matplotlib/contour.py:1120, post-patch at base_commit 6091437). Verdict FAITHFUL: no precondition-satisfying reachable input makes the model's postcondition disagree with the real repo behavior.

Checks performed:
- Spec region byte-identical: same-spec self-check PASSES (SAME). Model verifies under the pinned Nagini with --float-encoding=real (RC=0, 17.8s); default (uninterpreted-float) verify correctly errs on the auto_levels precondition, confirming the real fragment is exercised.
- Reachable-input equivalence, confirmed by replicating the patched selection + post-processing (interior filter, filled>=2, increasing checks):
  * bool line contour -> real=[0.5]; model (two_valued & !filled): [mid], with zmin<mid<zmax. For a bool field zmin=0,zmax=1, mid pinned by mid-zmin==zmax-mid => mid=0.5. Match.
  * bool filled -> real=[0,.5,1]; model (two_valued & filled): [zmin,mid,zmax], len==3, strictly increasing. Match.
  * continuous -> real=_autolev(7) multi-level; model (!two_valued): ToSeq(Result())==auto_levels(zmin,zmax) with len>1. Match.
- Abstraction soundness: two_valued <-> np.issubdtype(z.dtype,bool). A bool z can only take values {False,True} => zmin=0.0, zmax=1.0, so the real hardcoded lists [0,.5,1]/[.5] equal the model's [zmin,mid,zmax]/[mid] under the pinned-midpoint equation. filled<->self.filled (identity); has_explicit<->len(args)!=0 (identity); the branch under spec is not has_explicit, exactly the default block.
- Line-contour interior filter (levels>zmin)&(levels<zmax): only replaces self.levels with [zmin] when NO level is strictly interior. For bool line, 0.5 is interior and survives; for well-resolved continuous ranges interior ticks always exist. axiom_check.py reads post-filter cs.levels and asserts len>1 on well-resolved ranges (7 boundary + ~850 fuzz) and confirms the guard excludes the collapse regime (e.g. (1e-300,2e-300)->1 level). So the filter never induces drift on reachable inputs.
- Auto_levels axiom is the WEAKEST sufficient contract (len>1) scoped by the well-resolved guard (span>=1e-6 and >=1e-9*zmax and >=1e-9*(-zmin)); this is a scoping of the precondition, not a strengthening of the postcondition, and G-AX validates it against the real _autolev/MaxNLocator path. The tested range [0,1] clears the guard with margin.

Conclusion: the spec is scoped exactly to the real behavior on all reachable inputs; not too strong, no divergence. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** panel_3: leakage accepted per RELAXED_LEAKAGE.md (agent flagged: leakage)

**What the spec view discloses.** Quoted from this bundle's own `RELAXED_LEAKAGE.md`, "Any faithful, G-DIFF-failing spec must name the filled facet":

> The model's spec view discloses, in its docstring (model.py lines 24-26), "for a filled contour: the three levels `[zmin, midpoint, zmax]` ... a filled contour requires at least two levels", and the post-conditions pin `Implies(two_valued and filled, len(Result()) == 3)` / `Result()[0] == zmin and Result()[2] == zmax` / `len(Result()) >= 2`. These are load-bearing: the F2P test checks `plt.contourf(z).levels.tolist() == [0, .5, 1]` for all four filled forms; dropping them lets a wrong `contourf` impl verify.

**Why the disclosure is accepted.** The same file's account of why the disclosure is forced rather than avoidable, "Why the FILLED leak is genuinely unavoidable (not lazy de-narration)":

> The behaviour the gold actually fixes for `contourf` — and that the F2P test measures — IS the leaked discriminator. There is no way to pin it without naming the three-level / "at least two levels" filled default.

**What this role measured.** The disposition this role defers to is recorded rather than assumed: `meta.json` sets `relaxed_leakage: true`, the bundle ships the `RELAXED_LEAKAGE.md` quoted above, and `G-LEAK` records `relaxed` with the detail `semantic leak of gold discriminator; unavoidable for a faithful spec`. The file quoted here is byte-identical to the one that gate read (sha256 `3bfce752d83a`, recorded under `G-LEAK`'s own sources), and it carries no instruction to the role reviewing it -- a relaxation document that told this panel which verdict to submit would make `G-LEAK` record a failure instead of a relaxation, so the argument above is one this role judged rather than one it was handed.

`G-LEAK`'s lexical screen recorded no failures of its own, which is what places this disclosure in what the specification pins rather than in a word the spec view uses. This role is advisory and only `G-LEAK` is recorded for leakage on this cell, which is why the deferral is a pass here and not a status of its own. The panel submitted `LEAKAGE`; a non-empty verdict is required for the deferral to apply at all, so a review that never ran is recorded as reaching no verdict rather than as deferring to this file. The panel's own account -- whether it accepts the argument quoted above or presses further against it -- is published in this cell's audit record.

same_spec=TRUE (adversary same-spec exit 0; spec/axiom/pre/post regions byte-identical between model.py and model_prepatch.py, only impl differs). LEAKAGE finding: the public problem_statement discloses ONLY the LINE facet (bool array -> single level at 0.5; 'plt.contour(boolean_2d_array, levels=[.5])'). It NEVER mentions filled contours/contourf, the three-level [0,.5,1] default, or the 'at least 2 levels' rule. Those appear only in hints_text (explicitly excluded from the public view).

The spec view leaks the gold's FILLED branch (gold: `elif np.issubdtype(z_dtype, bool): if self.filled: levels_arg=[0,.5,1]`) via load-bearing postconditions pinning len==3, Result[0]==zmin, Result[2]==zmax, Result[1]==mid, len>=2, plus docstring lines 24-26 ('for a filled contour: the three levels [zmin, midpoint, zmax] ... a filled contour requires at least two levels'). This reconstructs the gold edit's filled facet beyond the public problem_statement. NOTE: bundle is relaxed_leakage=true with an ACCEPTED RELAXED_LEAKAGE.md (project decision 2026-06-14, PS<->gold mismatch on the filled facet; core soundness G-VERIFY/G-DIFF/G-EQ/G-AX intact, G-RESOLVE resolves).

Per the G-PANEL-3 deferral policy this LEAKAGE verdict on a relaxed bundle records pass+note rather than fail; the leak is real but documented and unavoidable (no problem_statement-derivable reformulation of the filled facet exists). Spec view correctly still avoids patched path/symbol names (_process_contour_level_args, np.issubdtype, z_dtype, contour.py).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded LEAKAGE. The record is a pass because the disclosure it names had already been accepted by a reviewer: an accepted relaxation is the leakage GATE's disposition to record, and this cell records G-LEAK as `relaxed`. This role defers to that disposition rather than re-failing the cell, and is recorded as a pass with a note because `relaxed` is not a status it may take. So the pass rests on an accepted disclosure and not on the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `model.py`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.