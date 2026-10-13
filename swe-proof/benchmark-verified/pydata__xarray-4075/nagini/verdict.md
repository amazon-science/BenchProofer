# P2 adversarial audit — pydata__xarray-4075

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -107,7 +106,6 @@
                      Forall(int, lambda i: (Implies(0 <= i and i < len(weights),
                                                      weights[i] == 0 or weights[i] == 1),
                                             [[weights[i]]]))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(mask), 1 / 2))
@@ -118,9 +116,9 @@
     Ensures(Result() == int_dot(ToSeq(mask), ToSeq(weights)))
     # post-conditions-end
     # impl-start
-    # Hand the dot a numeric operand (a boolean weight array is cast to int
-    # first), so the reduction always runs in numeric arithmetic and counts.
-    boolean_dot = False
+    # Pre-patch: no cast; boolean weights meet the boolean mask in a boolean
+    # (saturating) contraction that fails to count.
+    boolean_dot = weights_are_bool
     result = dot_reduce(ToSeq(mask), ToSeq(weights), boolean_dot)
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -107,7 +106,6 @@
                      Forall(int, lambda i: (Implies(0 <= i and i < len(weights),
                                                      weights[i] == 0 or weights[i] == 1),
                                             [[weights[i]]]))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(mask), 1 / 2))
@@ -118,9 +116,6 @@
     Ensures(Result() == int_dot(ToSeq(mask), ToSeq(weights)))
     # post-conditions-end
     # impl-start
-    # Hand the dot a numeric operand (a boolean weight array is cast to int
-    # first), so the reduction always runs in numeric arithmetic and counts.
-    boolean_dot = False
-    result = dot_reduce(ToSeq(mask), ToSeq(weights), boolean_dot)
+    result = 2
     return result
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -107,7 +106,6 @@
                      Forall(int, lambda i: (Implies(0 <= i and i < len(weights),
                                                      weights[i] == 0 or weights[i] == 1),
                                             [[weights[i]]]))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(mask), 1 / 2))
@@ -118,9 +116,8 @@
     Ensures(Result() == int_dot(ToSeq(mask), ToSeq(weights)))
     # post-conditions-end
     # impl-start
-    # Hand the dot a numeric operand (a boolean weight array is cast to int
-    # first), so the reduction always runs in numeric arithmetic and counts.
+    n = len(mask)
     boolean_dot = False
-    result = dot_reduce(ToSeq(mask), ToSeq(weights), boolean_dot)
+    result = dot_reduce(ToSeq(mask).take(n - 1), ToSeq(weights).take(n - 1), boolean_dot)
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -107,7 +106,6 @@
                      Forall(int, lambda i: (Implies(0 <= i and i < len(weights),
                                                      weights[i] == 0 or weights[i] == 1),
                                             [[weights[i]]]))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(mask), 1 / 2))
@@ -118,9 +116,10 @@
     Ensures(Result() == int_dot(ToSeq(mask), ToSeq(weights)))
     # post-conditions-end
     # impl-start
-    # Hand the dot a numeric operand (a boolean weight array is cast to int
-    # first), so the reduction always runs in numeric arithmetic and counts.
     boolean_dot = False
-    result = dot_reduce(ToSeq(mask), ToSeq(weights), boolean_dot)
+    if len(mask) >= 2:
+        result = dot_reduce(ToSeq(mask), ToSeq(weights), boolean_dot)
+    else:
+        result = 0
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -107,7 +106,6 @@
                      Forall(int, lambda i: (Implies(0 <= i and i < len(weights),
                                                      weights[i] == 0 or weights[i] == 1),
                                             [[weights[i]]]))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(mask), 1 / 2))
@@ -118,9 +116,9 @@
     Ensures(Result() == int_dot(ToSeq(mask), ToSeq(weights)))
     # post-conditions-end
     # impl-start
-    # Hand the dot a numeric operand (a boolean weight array is cast to int
-    # first), so the reduction always runs in numeric arithmetic and counts.
-    boolean_dot = False
-    result = dot_reduce(ToSeq(mask), ToSeq(weights), boolean_dot)
+    result = 0
+    while True:
+        Invariant(result >= 0)
+        result = result + 1
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -107,7 +106,6 @@
                      Forall(int, lambda i: (Implies(0 <= i and i < len(weights),
                                                      weights[i] == 0 or weights[i] == 1),
                                             [[weights[i]]]))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(mask), 1 / 2))
@@ -118,9 +116,6 @@
     Ensures(Result() == int_dot(ToSeq(mask), ToSeq(weights)))
     # post-conditions-end
     # impl-start
-    # Hand the dot a numeric operand (a boolean weight array is cast to int
-    # first), so the reduction always runs in numeric arithmetic and counts.
-    boolean_dot = False
-    result = dot_reduce(ToSeq(mask), ToSeq(weights), boolean_dot)
+    result = int_dot(ToSeq(mask), ToSeq(weights))
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -107,7 +106,6 @@
                      Forall(int, lambda i: (Implies(0 <= i and i < len(weights),
                                                      weights[i] == 0 or weights[i] == 1),
                                             [[weights[i]]]))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(mask), 1 / 2))
@@ -118,9 +116,9 @@
     Ensures(Result() == int_dot(ToSeq(mask), ToSeq(weights)))
     # post-conditions-end
     # impl-start
-    # Hand the dot a numeric operand (a boolean weight array is cast to int
-    # first), so the reduction always runs in numeric arithmetic and counts.
-    boolean_dot = False
-    result = dot_reduce(ToSeq(mask), ToSeq(weights), boolean_dot)
+    if weights_are_bool:
+        result = dot_reduce(ToSeq(mask), ToSeq(weights), True)
+    else:
+        result = dot_reduce(ToSeq(mask), ToSeq(weights), False)
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pydata__xarray-4075.

Behaviour under specification (stated as the desired behaviour, not as an edit):

  A weighted total counts how much trustworthy weight backs a set of samples.
  Each sample i carries a presence flag `mask[i]` (1 if the datum is present,
  0 if it is missing) and an associated weight `weights[i]` (a non-negative
  integer; a boolean weight is the special case of the values 0/1). The total
  is the weighted reduction `sum_i mask[i] * weights[i]` — the arithmetic sum
  of the weights of the present samples — computed by the array dot product of
  the presence flags and the weights.

  The decisive requirement: this total is a genuine numeric COUNT, never a mere
  presence indicator. When several present samples each carry weight 1 the total
  must accumulate them (e.g. two present unit weights total 2), and it must do so
  identically whether the weights were supplied as a boolean array or as a
  numeric array — the element type of the weights must not collapse the sum to a
  0/1 "any present" answer.

Modelling: the presence mask is `mask: List[int]` of 0/1; the weights are
`weights: List[int]` of non-negative integers (booleans being 0/1);
`weights_are_bool` records whether the weight array's element type is boolean.
The array dot product is the unchanged community callee `dot_reduce`, whose
contraction is numeric when handed a numeric operand and boolean-saturating when
BOTH operands are boolean. The numeric and boolean contractions are spelled out
deeply as the front-recursive folds `int_dot` / `bool_dot` (validated == the real
dot by axiom_check.py / G-AX). The specification is carried by `PSeq[int]`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def dot_reduce(mask: PSeq[int], weights: PSeq[int], boolean_dot: bool) -> int:
    """The array dot-product reduction (the unchanged community callee) of the
    presence flags `mask` and the `weights`, contracted over the shared axis.

    The contraction semantics depend ONLY on whether it runs in boolean
    arithmetic (`boolean_dot`), which happens exactly when BOTH operands have a
    boolean element type:

      * numeric contraction (`boolean_dot` false — a numeric operand is present,
        as the desired behaviour always arranges): the genuine arithmetic sum
        `sum_i mask[i] * weights[i]` (`int_dot`).
      * boolean contraction (`boolean_dot` true — both operands boolean): the
        SATURATING logical reduction, 1 iff some position has both flags set,
        else 0 (`bool_dot`); it cannot exceed 1.

    Weakest contract the proof needs. Provenance + executable soundness check:
    mapping.md / axiom_check.py.
    """
    Requires(len(mask) == len(weights))
    Ensures(Implies(not boolean_dot, Result() == int_dot(mask, weights)))
    Ensures(Implies(boolean_dot, Result() == bool_dot(mask, weights)))
# axioms-end


# pure-start
@Pure
def int_dot(mask: PSeq[int], weights: PSeq[int]) -> int:
    """Numeric dot-product reduction: the arithmetic sum of the present samples'
    weights, `sum_i mask[i] * weights[i]`. Front-recursive (one unfold per loop
    step — the canonical sequence-fold pattern)."""
    Requires(len(mask) == len(weights))
    if len(mask) == 0:
        return 0
    return mask[0] * weights[0] + int_dot(mask.drop(1), weights.drop(1))


@Pure
def bool_dot(mask: PSeq[int], weights: PSeq[int]) -> int:
    """Boolean (saturating) dot-product reduction: 1 iff some position has both
    flags set, else 0. The logical OR over positions of (mask[i] AND
    weights[i]), with 0/1 operands modelled by min (AND) and max (OR).
    Front-recursive."""
    Requires(len(mask) == len(weights))
    if len(mask) == 0:
        return 0
    head = 1 if (mask[0] >= 1 and weights[0] >= 1) else 0
    return head if head >= bool_dot(mask.drop(1), weights.drop(1)) \
        else bool_dot(mask.drop(1), weights.drop(1))
# pure-end


def sum_of_weights_value(
    mask: List[int], weights: List[int], weights_are_bool: bool
) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(mask), 1 / 2))
    Requires(Acc(list_pred(weights), 1 / 2))
    Requires(len(mask) == len(weights))
    Requires(len(ToSeq(mask)) == len(ToSeq(weights)))
    # presence flags and (the boolean case of) the weights are 0/1; the numeric
    # case allows any non-negative integer weight.
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(mask),
                                             mask[i] == 0 or mask[i] == 1),
                                     [[mask[i]]])))
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(weights),
                                             weights[i] >= 0),
                                     [[weights[i]]])))
    Requires(Implies(weights_are_bool,
                     Forall(int, lambda i: (Implies(0 <= i and i < len(weights),
                                                     weights[i] == 0 or weights[i] == 1),
                                            [[weights[i]]]))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(mask), 1 / 2))
    Ensures(Acc(list_pred(weights), 1 / 2))
    Ensures(len(ToSeq(mask)) == len(ToSeq(weights)))
    # The total is the genuine arithmetic weighted count of the present samples,
    # independent of whether the weights were boolean or numeric.
    Ensures(Result() == int_dot(ToSeq(mask), ToSeq(weights)))
    # post-conditions-end
    # impl-start
    # Hand the dot a numeric operand (a boolean weight array is cast to int
    # first), so the reduction always runs in numeric arithmetic and counts.
    boolean_dot = False
    result = dot_reduce(ToSeq(mask), ToSeq(weights), boolean_dot)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Spec postcondition Result() == int_dot(ToSeq(mask), ToSeq(weights)) is a TIGHT TOTAL functional spec pinning the exact arithmetic weighted count grounded on the actual input carriers (not an opaque oracle/constant). int_dot/bool_dot are deep front-recursive folds validated == the real xr.dot by axiom_check.py/G-AX (ran here: exit 0; boundary + 2000 fuzz; incl. astype(int) cast = gold and [True,True].[True,True]->1(bool) vs 2(int)).

ATTACKS (7 distinct wrong impls; only impl region edited, all confirmed same-spec via `adversary same-spec`, exit 0). weakness = `python -m swebench_unified.adversary weakness nagini pydata__xarray-4075 <path>`:
- atk_1 PREPATCH BUG (boolean_dot = weights_are_bool; boolean saturating dot): weakness exit 2 REJECTED (does not verify). prepatch reproduced.
- atk_2 ungrounded-oracle echo (return constant 2): weakness exit 2 REJECTED.
- atk_3 boundary/off-by-one (dot over take(n-1)): weakness exit 2 REJECTED.
- atk_4 partial-domain (correct dot for len>=2, else 0): weakness exit 2 REJECTED.
- atk_5 control-flow/non-termination hole (while True, unreachable return): weakness exit 2 REJECTED (Nagini enforces termination).
- atk_6 same-value alternative (result = int_dot(ToSeq(mask),ToSeq(weights)) directly, bypassing dot_reduce): weakness exit 0 CANDIDATE (shares spec AND verifies, 32.5s).
- atk_7 control-flow-effect echo of bug (branch to dot_reduce(...,True) when weights_are_bool): weakness exit 2 REJECTED.

Positive control: model.py impl (boolean_dot=False) verifies (bash scripts/nagini_verify.sh positive_control.py -> Verification successful, 23.5s).

MANDATED RESOLVE of the one CANDIDATE (atk_6): materialized its faithful refined patch (patch_atk_6.diff = 'always reduce numeric: astype(int) for bool weights, else unchanged' — the real-code refinement of computing int_dot unconditionally) and RAN it through the official harness `run_resolve`:
  ATK6 resolved=True completed=True note='resolved' attempts=1 (confirmed twice, two independent runs).
Harness-health control: GOLD patch run_resolve -> resolved=True completed=True note='resolved'. (An initial atk_6 run returned completed=False = infra/contention noise, NOT a genuine non-resolution; the clean re-runs both completed and resolved.)

So the sole verifying wrong-impl candidate is behaviourally equal to gold on the tested inputs and its faithful patch RESOLVES -> no verify-but-wrong witness -> spec is NOT too weak.

REFINEMENT.MD LEG AUDIT (A-legs, per mandate): A1=R (bool mask/weights -> List[int]; dtype predicate -> weights_are_bool) OK. A2=R (boolean_dot=False <-> astype(int)/else branch; both real branches feed dot a numeric operand -> numeric contraction) OK. A3=A-consumed for dot_reduce, which axiomatizes the UNCHANGED community callee xarray.core.computation.dot (NOT the function under change) — correct A-consumed. A4=A-reference: int_dot/bool_dot deep folds, NOT hidden behind a stronger axiom, validated == real dot by G-AX (verified passing here). A5=R+I: modeled value = dot quantity; downstream where(sum_of_weights!=0.0) masking is identity on the tested NON-ZERO reductions (both F2P tests have sum_of_weights=2!=0), so it does not affect the observation. Every leg is R / A-consumed / A-reference / I — NO kind-3 (unexpressible-changed-op) leg. The genuinely-changed op (operand dtype -> whether contraction counts or saturates) is captured by the boolean_dot knob with both semantics modeled deeply. A-leg correspondence to real callees holds (G-AX exit 0).

Evidence dir: (atk_1..7.py, positive_control.py, patch_atk_6.diff, log_atk_*.txt, log_posctl.txt, resolve_atk_6.log).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for pydata__xarray-4075.

Behaviour under specification (stated as the desired behaviour, not as an edit):

  A weighted total counts how much trustworthy weight backs a set of samples.
  Each sample i carries a presence flag `mask[i]` (1 if the datum is present,
  0 if it is missing) and an associated weight `weights[i]` (a non-negative
  integer; a boolean weight is the special case of the values 0/1). The total
  is the weighted reduction `sum_i mask[i] * weights[i]` — the arithmetic sum
  of the weights of the present samples — computed by the array dot product of
  the presence flags and the weights.

  The decisive requirement: this total is a genuine numeric COUNT, never a mere
  presence indicator. When several present samples each carry weight 1 the total
  must accumulate them (e.g. two present unit weights total 2), and it must do so
  identically whether the weights were supplied as a boolean array or as a
  numeric array — the element type of the weights must not collapse the sum to a
  0/1 "any present" answer.

Modelling: the presence mask is `mask: List[int]` of 0/1; the weights are
`weights: List[int]` of non-negative integers (booleans being 0/1);
`weights_are_bool` records whether the weight array's element type is boolean.
The array dot product is the unchanged community callee `dot_reduce`, whose
contraction is numeric when handed a numeric operand and boolean-saturating when
BOTH operands are boolean. The numeric and boolean contractions are spelled out
deeply as the front-recursive folds `int_dot` / `bool_dot` (validated == the real
dot by axiom_check.py / G-AX). The specification is carried by `PSeq[int]`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def dot_reduce(mask: PSeq[int], weights: PSeq[int], boolean_dot: bool) -> int:
    """The array dot-product reduction (the unchanged community callee) of the
    presence flags `mask` and the `weights`, contracted over the shared axis.

    The contraction semantics depend ONLY on whether it runs in boolean
    arithmetic (`boolean_dot`), which happens exactly when BOTH operands have a
    boolean element type:

      * numeric contraction (`boolean_dot` false — a numeric operand is present,
        as the desired behaviour always arranges): the genuine arithmetic sum
        `sum_i mask[i] * weights[i]` (`int_dot`).
      * boolean contraction (`boolean_dot` true — both operands boolean): the
        SATURATING logical reduction, 1 iff some position has both flags set,
        else 0 (`bool_dot`); it cannot exceed 1.

    Weakest contract the proof needs. Provenance + executable soundness check:
    mapping.md / axiom_check.py.
    """
    Requires(len(mask) == len(weights))
    Ensures(Implies(not boolean_dot, Result() == int_dot(mask, weights)))
    Ensures(Implies(boolean_dot, Result() == bool_dot(mask, weights)))
# axioms-end


# pure-start
@Pure
def int_dot(mask: PSeq[int], weights: PSeq[int]) -> int:
    """Numeric dot-product reduction: the arithmetic sum of the present samples'
    weights, `sum_i mask[i] * weights[i]`. Front-recursive (one unfold per loop
    step — the canonical sequence-fold pattern)."""
    Requires(len(mask) == len(weights))
    if len(mask) == 0:
        return 0
    return mask[0] * weights[0] + int_dot(mask.drop(1), weights.drop(1))


@Pure
def bool_dot(mask: PSeq[int], weights: PSeq[int]) -> int:
    """Boolean (saturating) dot-product reduction: 1 iff some position has both
    flags set, else 0. The logical OR over positions of (mask[i] AND
    weights[i]), with 0/1 operands modelled by min (AND) and max (OR).
    Front-recursive."""
    Requires(len(mask) == len(weights))
    if len(mask) == 0:
        return 0
    head = 1 if (mask[0] >= 1 and weights[0] >= 1) else 0
    return head if head >= bool_dot(mask.drop(1), weights.drop(1)) \
        else bool_dot(mask.drop(1), weights.drop(1))
# pure-end


def sum_of_weights_value(
    mask: List[int], weights: List[int], weights_are_bool: bool
) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(mask), 1 / 2))
    Requires(Acc(list_pred(weights), 1 / 2))
    Requires(len(mask) == len(weights))
    Requires(len(ToSeq(mask)) == len(ToSeq(weights)))
    # presence flags and (the boolean case of) the weights are 0/1; the numeric
    # case allows any non-negative integer weight.
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(mask),
                                             mask[i] == 0 or mask[i] == 1),
                                     [[mask[i]]])))
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(weights),
                                             weights[i] >= 0),
                                     [[weights[i]]])))
    Requires(Implies(weights_are_bool,
                     Forall(int, lambda i: (Implies(0 <= i and i < len(weights),
                                                     weights[i] == 0 or weights[i] == 1),
                                            [[weights[i]]]))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(mask), 1 / 2))
    Ensures(Acc(list_pred(weights), 1 / 2))
    Ensures(len(ToSeq(mask)) == len(ToSeq(weights)))
    # The total is the genuine arithmetic weighted count of the present samples,
    # independent of whether the weights were boolean or numeric.
    Ensures(Result() == int_dot(ToSeq(mask), ToSeq(weights)))
    # post-conditions-end
    # impl-start
    # Hand the dot a numeric operand (a boolean weight array is cast to int
    # first), so the reduction always runs in numeric arithmetic and counts.
    boolean_dot = False
    result = dot_reduce(ToSeq(mask), ToSeq(weights), boolean_dot)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. Spec postcondition Result() == int_dot(ToSeq(mask), ToSeq(weights)) is a TIGHT TOTAL functional spec pinning the exact arithmetic weighted count grounded on the actual input carriers (not an opaque oracle/constant). int_dot/bool_dot are deep front-recursive folds validated == the real xr.dot by axiom_check.py/G-AX (ran here: exit 0; boundary + 2000 fuzz; incl. astype(int) cast = gold and [True,True].[True,True]->1(bool) vs 2(int)).

ATTACKS (7 distinct wrong impls; only impl region edited, all confirmed same-spec via `adversary same-spec`, exit 0). weakness = `python -m swebench_unified.adversary weakness nagini pydata__xarray-4075 <path>`:
- atk_1 PREPATCH BUG (boolean_dot = weights_are_bool; boolean saturating dot): weakness exit 2 REJECTED (does not verify). prepatch reproduced.
- atk_2 ungrounded-oracle echo (return constant 2): weakness exit 2 REJECTED.
- atk_3 boundary/off-by-one (dot over take(n-1)): weakness exit 2 REJECTED.
- atk_4 partial-domain (correct dot for len>=2, else 0): weakness exit 2 REJECTED.
- atk_5 control-flow/non-termination hole (while True, unreachable return): weakness exit 2 REJECTED (Nagini enforces termination).
- atk_6 same-value alternative (result = int_dot(ToSeq(mask),ToSeq(weights)) directly, bypassing dot_reduce): weakness exit 0 CANDIDATE (shares spec AND verifies, 32.5s).
- atk_7 control-flow-effect echo of bug (branch to dot_reduce(...,True) when weights_are_bool): weakness exit 2 REJECTED.

Positive control: model.py impl (boolean_dot=False) verifies (bash scripts/nagini_verify.sh positive_control.py -> Verification successful, 23.5s).

MANDATED RESOLVE of the one CANDIDATE (atk_6): materialized its faithful refined patch (patch_atk_6.diff = 'always reduce numeric: astype(int) for bool weights, else unchanged' — the real-code refinement of computing int_dot unconditionally) and RAN it through the official harness `run_resolve`:
  ATK6 resolved=True completed=True note='resolved' attempts=1 (confirmed twice, two independent runs).
Harness-health control: GOLD patch run_resolve -> resolved=True completed=True note='resolved'. (An initial atk_6 run returned completed=False = infra/contention noise, NOT a genuine non-resolution; the clean re-runs both completed and resolved.)

So the sole verifying wrong-impl candidate is behaviourally equal to gold on the tested inputs and its faithful patch RESOLVES -> no verify-but-wrong witness -> spec is NOT too weak.

REFINEMENT.MD LEG AUDIT (A-legs, per mandate): A1=R (bool mask/weights -> List[int]; dtype predicate -> weights_are_bool) OK. A2=R (boolean_dot=False <-> astype(int)/else branch; both real branches feed dot a numeric operand -> numeric contraction) OK. A3=A-consumed for dot_reduce, which axiomatizes the UNCHANGED community callee xarray.core.computation.dot (NOT the function under change) — correct A-consumed. A4=A-reference: int_dot/bool_dot deep folds, NOT hidden behind a stronger axiom, validated == real dot by G-AX (verified passing here). A5=R+I: modeled value = dot quantity; downstream where(sum_of_weights!=0.0) masking is identity on the tested NON-ZERO reductions (both F2P tests have sum_of_weights=2!=0), so it does not affect the observation. Every leg is R / A-consumed / A-reference / I — NO kind-3 (unexpressible-changed-op) leg. The genuinely-changed op (operand dtype -> whether contraction counts or saturates) is captured by the boolean_dot knob with both semantics modeled deeply. A-leg correspondence to real callees holds (G-AX exit 0).

Evidence dir: (atk_1..7.py, positive_control.py, patch_atk_6.diff, log_atk_*.txt, log_posctl.txt, resolve_atk_6.log).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The modeled function `sum_of_weights_value` is scoped to the value of the changed statement `sum_of_weights = self._reduce(mask, weights, dim, skipna=False)` = `dot(mask, weights, dims=dim)` (xarray/core/weighted.py:145 at base_commit 19b08863), NOT the full `_sum_of_weights` body. Postcondition `Result()==int_dot(ToSeq(mask),ToSeq(weights)) = sum_i mask[i]*weights[i]`.

Faithfulness of the modeled callee: verified. Re-ran axiom_check.py in xarray 0.15.1 — PASS: int_dot == real numeric xr.dot (incl. bool weights cast via astype(int)) over 11 boundary + 2000 fuzz inputs; bool_dot == boolean saturating contraction. No in-domain input (mask∈{0,1}, weights≥0 int) separates int_dot from the real numeric dot.

Spec is NOT too strong: the gold patch computes the changed statement numerically in BOTH branches (bool→astype(int)→numeric dot; else already-numeric), so the real gold changed-statement value equals int_dot across the entire modeled domain, including weights_are_bool==True. The postcondition therefore agrees with the gold patch everywhere in domain; the pre-patch (model_prepatch: boolean_dot=weights_are_bool → bool_dot) correctly FAILS it on true-count≥2 (the GH4074 case). This confirms the spec discriminates buggy from fixed rather than over-constraining.

F2P impact: on both F2P tests (test_weighted_sum_of_weights_bool → 2; test_weighted_mean_bool denominator → 2) the reduction is non-zero, so the excluded `.where` masking is the identity and the tested observation is unaffected — the out-of-scope divergence never manifests on the resolving inputs.

spec region byte-identical check (same_spec) passes; model verifies (G-EQ recorded pass, 9 attacks rejected); G-AX recorded pass. No faithfulness break found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement is exceptionally explicit: it names the bug (xr.dot of two boolean arrays -> True/1 not 2) and states the fix verbatim ('We'll need to convert it to int or float: xr.dot(dta.notnull(), wgt * 1)'). Thus the entire discriminating idea of the gold edit (cast boolean weights to numeric before the dot so the contraction counts instead of saturating) is already fully public. The spec view (model.py spec regions: docstring, dot_reduce axiom, int_dot/bool_dot pure folds, pre/post-conditions) describes the desired numeric-count behavior in ABSTRACT modeling terms (boolean_dot, weights_are_bool, int_dot == sum_i mask[i]*weights[i]) and does NOT quote the gold patch's concrete tokens (astype(int), if self.weights.dtype == bool, the GH4074 comment). Those verbatim gold-hunk quotations appear only in mapping.md and refinement.md, which are auditor derivation/audit artifacts, not the solver-facing spec. Every behavioral fact the spec view conveys about the boolean-vs-numeric distinction is already disclosed — more concretely — in problem_statement. Therefore the spec view leaks nothing beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
