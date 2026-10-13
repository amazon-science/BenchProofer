# P2 adversarial audit — scikit-learn__scikit-learn-26194

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_4.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
     # sequence is non-empty. Read-only input: fractional permission.
     Requires(Acc(list_pred(thresholds), 1 / 2))
     Requires(len(thresholds) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(thresholds), 1 / 2))
@@ -76,7 +74,8 @@
     Ensures(ToSeq(Result()).drop(1) == ToSeq(thresholds))
     # post-conditions-end
     # impl-start
-    lead = pos_inf()
+    # ATTACK-1 (prepatch bug): finite anchor thresholds[0]+1.0 instead of +inf.
+    lead = thresholds[0] + 1.0
     result = [lead]  # type: List[float]
     i = 0
     while i < len(thresholds):
@@ -85,10 +84,7 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(thresholds))
         Invariant(len(result) == i + 1)
-        Invariant(ToSeq(result).take(1) == PSeq(lead))
-        Invariant(is_pos_inf(ToSeq(result)[0]))
         Invariant(ToSeq(result).drop(1) == ToSeq(thresholds).take(i))
-        Invariant(MustTerminate(len(thresholds) - i + 1))
         # invariants-end
         result.append(thresholds[i])
         i = i + 1
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
     # sequence is non-empty. Read-only input: fractional permission.
     Requires(Acc(list_pred(thresholds), 1 / 2))
     Requires(len(thresholds) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(thresholds), 1 / 2))
@@ -76,19 +74,16 @@
     Ensures(ToSeq(Result()).drop(1) == ToSeq(thresholds))
     # post-conditions-end
     # impl-start
-    lead = pos_inf()
-    result = [lead]  # type: List[float]
+    # ATTACK-2 (boundary): forget to prepend the anchor; just copy thresholds.
+    result = []  # type: List[float]
     i = 0
     while i < len(thresholds):
         # invariants-start
         Invariant(Acc(list_pred(thresholds), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(thresholds))
-        Invariant(len(result) == i + 1)
-        Invariant(ToSeq(result).take(1) == PSeq(lead))
-        Invariant(is_pos_inf(ToSeq(result)[0]))
-        Invariant(ToSeq(result).drop(1) == ToSeq(thresholds).take(i))
-        Invariant(MustTerminate(len(thresholds) - i + 1))
+        Invariant(len(result) == i)
+        Invariant(ToSeq(result) == ToSeq(thresholds).take(i))
         # invariants-end
         result.append(thresholds[i])
         i = i + 1
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
     # sequence is non-empty. Read-only input: fractional permission.
     Requires(Acc(list_pred(thresholds), 1 / 2))
     Requires(len(thresholds) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(thresholds), 1 / 2))
@@ -76,6 +74,7 @@
     Ensures(ToSeq(Result()).drop(1) == ToSeq(thresholds))
     # post-conditions-end
     # impl-start
+    # ATTACK-3 (control-flow): correct anchor but each threshold appended twice.
     lead = pos_inf()
     result = [lead]  # type: List[float]
     i = 0
@@ -84,12 +83,9 @@
         Invariant(Acc(list_pred(thresholds), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(thresholds))
-        Invariant(len(result) == i + 1)
-        Invariant(ToSeq(result).take(1) == PSeq(lead))
         Invariant(is_pos_inf(ToSeq(result)[0]))
-        Invariant(ToSeq(result).drop(1) == ToSeq(thresholds).take(i))
-        Invariant(MustTerminate(len(thresholds) - i + 1))
         # invariants-end
+        result.append(thresholds[i])
         result.append(thresholds[i])
         i = i + 1
     return result
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
     # sequence is non-empty. Read-only input: fractional permission.
     Requires(Acc(list_pred(thresholds), 1 / 2))
     Requires(len(thresholds) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(thresholds), 1 / 2))
@@ -76,7 +74,10 @@
     Ensures(ToSeq(Result()).drop(1) == ToSeq(thresholds))
     # post-conditions-end
     # impl-start
-    lead = pos_inf()
+    # ATTACK-4 (ungrounded-oracle echo): same value as gold, different shape.
+    # Introduce a local infinite sentinel via pos_inf(), assign through a temp.
+    tmp = pos_inf()
+    lead = tmp
     result = [lead]  # type: List[float]
     i = 0
     while i < len(thresholds):
@@ -88,7 +89,6 @@
         Invariant(ToSeq(result).take(1) == PSeq(lead))
         Invariant(is_pos_inf(ToSeq(result)[0]))
         Invariant(ToSeq(result).drop(1) == ToSeq(thresholds).take(i))
-        Invariant(MustTerminate(len(thresholds) - i + 1))
         # invariants-end
         result.append(thresholds[i])
         i = i + 1
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
     # sequence is non-empty. Read-only input: fractional permission.
     Requires(Acc(list_pred(thresholds), 1 / 2))
     Requires(len(thresholds) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(thresholds), 1 / 2))
@@ -76,21 +74,18 @@
     Ensures(ToSeq(Result()).drop(1) == ToSeq(thresholds))
     # post-conditions-end
     # impl-start
+    # ATTACK-5 (control-flow): correct anchor but tail copied in REVERSE order.
     lead = pos_inf()
     result = [lead]  # type: List[float]
-    i = 0
-    while i < len(thresholds):
+    i = len(thresholds)
+    while i > 0:
         # invariants-start
         Invariant(Acc(list_pred(thresholds), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(thresholds))
-        Invariant(len(result) == i + 1)
-        Invariant(ToSeq(result).take(1) == PSeq(lead))
         Invariant(is_pos_inf(ToSeq(result)[0]))
-        Invariant(ToSeq(result).drop(1) == ToSeq(thresholds).take(i))
-        Invariant(MustTerminate(len(thresholds) - i + 1))
         # invariants-end
+        i = i - 1
         result.append(thresholds[i])
-        i = i + 1
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
     # sequence is non-empty. Read-only input: fractional permission.
     Requires(Acc(list_pred(thresholds), 1 / 2))
     Requires(len(thresholds) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(thresholds), 1 / 2))
@@ -76,6 +74,8 @@
     Ensures(ToSeq(Result()).drop(1) == ToSeq(thresholds))
     # post-conditions-end
     # impl-start
+    # ATTACK-6 (boundary): prepend inf, copy tail, but also append an EXTRA inf
+    # (length off by one; tail no longer equals thresholds).
     lead = pos_inf()
     result = [lead]  # type: List[float]
     i = 0
@@ -84,13 +84,10 @@
         Invariant(Acc(list_pred(thresholds), 1 / 2))
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(thresholds))
-        Invariant(len(result) == i + 1)
-        Invariant(ToSeq(result).take(1) == PSeq(lead))
         Invariant(is_pos_inf(ToSeq(result)[0]))
-        Invariant(ToSeq(result).drop(1) == ToSeq(thresholds).take(i))
-        Invariant(MustTerminate(len(thresholds) - i + 1))
         # invariants-end
         result.append(thresholds[i])
         i = i + 1
+    result.append(pos_inf())
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -28,7 +28,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -63,7 +62,6 @@
     # sequence is non-empty. Read-only input: fractional permission.
     Requires(Acc(list_pred(thresholds), 1 / 2))
     Requires(len(thresholds) >= 1)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(thresholds), 1 / 2))
@@ -76,7 +74,9 @@
     Ensures(ToSeq(Result()).drop(1) == ToSeq(thresholds))
     # post-conditions-end
     # impl-start
-    lead = pos_inf()
+    # ATTACK-7 (ungrounded oracle): lead = thresholds[0], a finite value; try to
+    # claim is_pos_inf without pos_inf() grounding.
+    lead = thresholds[0]
     result = [lead]  # type: List[float]
     i = 0
     while i < len(thresholds):
@@ -85,10 +85,7 @@
         Invariant(Acc(list_pred(result)))
         Invariant(0 <= i and i <= len(thresholds))
         Invariant(len(result) == i + 1)
-        Invariant(ToSeq(result).take(1) == PSeq(lead))
-        Invariant(is_pos_inf(ToSeq(result)[0]))
         Invariant(ToSeq(result).drop(1) == ToSeq(thresholds).take(i))
-        Invariant(MustTerminate(len(thresholds) - i + 1))
         # invariants-end
         result.append(thresholds[i])
         i = i + 1
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-26194.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A receiver-operating-characteristic computation finishes by prepending one
  extra leading entry to the descending sequence of decision thresholds, so the
  plotted curve is anchored at the origin (the leading entry corresponds to the
  degenerate operating point where no instance is predicted positive).

  The desired leading threshold is the POSITIVE-INFINITY sentinel: a single
  value that is correct regardless of the scale of the scores (which may be
  arbitrary decision values or probability estimates confined to the unit
  interval). The remaining thresholds are returned unchanged and in the same
  order.

So, given the finite descending thresholds `thresholds`, the result is the list
whose first element is the positive-infinity sentinel and whose remaining
elements are exactly `thresholds` in order.

The thresholds are modelled as a `List[float]` of interpreted real numbers
(verified with `--float-encoding=real`), since the distinguishing behaviour is
the real-number identity of the anchoring entry. Two unchanged numeric
primitives carry the infinity theory: `pos_inf` is the positive-infinity
sentinel and `is_pos_inf` tests whether a real number is that sentinel; their
provenance and executable soundness check are in mapping.md / axiom_check.py.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def is_pos_inf(x: float) -> bool:
    """Test whether a real number is the positive-infinity sentinel. An unchanged
    numeric primitive (the is-infinite test) the routine relies on; opaque
    predicate. Provenance + executable soundness check: mapping.md /
    axiom_check.py."""
    pass

@Pure
@ContractOnly
def pos_inf() -> float:
    """The positive-infinity sentinel. An unchanged numeric primitive the routine
    prepends as the anchoring threshold; it satisfies `is_pos_inf`. Provenance +
    executable soundness check: mapping.md / axiom_check.py."""
    Ensures(is_pos_inf(Result()))
# axioms-end

# pure-start
# (no pure helpers needed)
# pure-end

def anchor_thresholds(thresholds: List[float]) -> List[float]:
    # pre-conditions-start
    # The descending decision thresholds are the distinct finite scores; the
    # sequence is non-empty. Read-only input: fractional permission.
    Requires(Acc(list_pred(thresholds), 1 / 2))
    Requires(len(thresholds) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(thresholds), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Exactly one extra leading entry is prepended.
    Ensures(len(Result()) == len(thresholds) + 1)
    # The leading anchoring threshold is the positive-infinity sentinel.
    Ensures(is_pos_inf(Result()[0]))
    # Every remaining threshold is returned unchanged, in the same order.
    Ensures(ToSeq(Result()).drop(1) == ToSeq(thresholds))
    # post-conditions-end
    # impl-start
    lead = pos_inf()
    result = [lead]  # type: List[float]
    i = 0
    while i < len(thresholds):
        # invariants-start
        Invariant(Acc(list_pred(thresholds), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(thresholds))
        Invariant(len(result) == i + 1)
        Invariant(ToSeq(result).take(1) == PSeq(lead))
        Invariant(is_pos_inf(ToSeq(result)[0]))
        Invariant(ToSeq(result).drop(1) == ToSeq(thresholds).take(i))
        # invariants-end
        result.append(thresholds[i])
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. FROZEN spec pins the output completely: len(Result())==len(thresholds)+1, is_pos_inf(Result()[0]) (the opaque predicate's ONLY known fact is pos_inf()'s Ensures(is_pos_inf(Result())), so Result()[0] must provably equal pos_inf()), and ToSeq(Result()).drop(1)==ToSeq(thresholds) (exact tail equality, in order). Thus any verifying same-spec impl must yield [pos_inf()]+thresholds, which refines to np.r_[np.inf, thresholds] = gold hunk.

Protocol executed Positive control (bundle model.py) verifies (10.2s, nagini_verify.sh exit 0). Prepatch reproduced: bundle model_prepatch.py (lead=thresholds[0]+1.0) FAILS on 'Postcondition ... Assertion is_pos_inf(Result()[0]) might not hold' (nagini_verify exit 1) — spec senses the change (G-DIFF).

7 distinct same-spec wrong impls built (impl-region-only edits; axioms/@Pure/Requires/Ensures byte-identical; confirmed SAME by `adversary same-spec` for all 7). Ran `adversary weakness nagini scikit-learn__scikit-learn-26194 <atk>` in parallel batches of <=3 (each spawns JVM+Z3):
  atk_1 prepatch-bug (finite thresholds[0]+1.0): same-spec, NOT verify (rejected — is_pos_inf fails).
  atk_2 boundary (no prepend; result=[]): same-spec, NOT verify (rejected — length/is_pos_inf fail).
  atk_3 control-flow-effect (correct anchor, tail appended twice): same-spec, NOT verify (rejected — length/tail fail).
  atk_4 ungrounded-oracle echo (lead=pos_inf() via temp, otherwise gold shape): same-spec AND VERIFIES (11.4s) => CANDIDATE.
  atk_5 control-flow-effect (correct anchor, tail copied in REVERSE): same-spec, NOT verify (rejected — tail!=thresholds).
  atk_6 boundary (correct prepend then extra trailing pos_inf(); len+1): same-spec, NOT verify (rejected — length/tail fail).
  atk_7 ungrounded oracle (lead=thresholds[0], finite, no pos_inf grounding): same-spec, NOT verify (rejected — is_pos_inf fails).

atk_4 is the ONLY CANDIDATE and is a semantic ECHO of the gold: it assigns lead=pos_inf() through a temp and does the identical forward copy, so its FAITHFUL refined patch is exactly the gold transform thresholds=np.r_[np.inf, thresholds]. Per protocol I MATERIALIZED that faithful patch (atk_4_faithful.patch) and RAN it through the official harness: run_resolve('scikit-learn__scikit-learn-26194', patch, timeout=1800) => RESOLVED: True, completed: True (Docker oracle, docker). A resolving same-spec echo is NOT a weakness (2026-08-06 G-PANEL-1/G-EQ policy: candidate breaks only if its refined patch does NOT resolve). No verifying wrong impl's faithful patch fails to resolve => verify=>correct holds.

refinement.md audit: A1=R (ndarray of float <-> List[float]; thresholds[k]<->thresholds[k], len<->len). A2=A-consumed (pos_inf <-> numpy.inf; proof consumes Ensures(is_pos_inf(Result())) to discharge anchoring post-condition; G-AX asserts np.isinf(np.inf), np.inf>0). A3=R+I (np.r_[x,arr] <-> [x]+list(arr); structural clauses len+1 and ToSeq(Result()).drop(1)==ToSeq(thresholds)). A4=A-consumed (is_pos_inf <-> numpy.isinf; the F2P discriminator np.isinf(thresholds[0])). No kind-3 (unexpressible-changed-op) steps: the one genuinely-changed operation (which scalar is prepended) is modeled DIRECTLY in the impl (lead=pos_inf()), not hidden behind an axiom of the function-under-change (roc_curve is NOT axiomatized). The two consumed axioms cover UNCHANGED numpy primitives (np.inf/np.isinf); their soundness/correspondence is audited by axiom_check.py against the real callees and real roc_curve. A-leg correspondence to real callees holds. Every leg is R / A-consumed / I.

Commands (project root; python=python; concurrent runs HOME env):
  same-spec: python -m swebench_unified.adversary same-spec nagini scikit-learn__scikit-learn-26194 atk_N.py (all 7 => SAME, exit 0)
  weakness:  python -m swebench_unified.adversary weakness  nagini scikit-learn__scikit-learn-26194 atk_N.py (atk_4 => CANDIDATE exit 0; atk_1,2,3,5,6,7 => NOT-A-COUNTEREXAMPLE/does-not-verify exit 2)
  positive control: bash scripts/nagini_verify.sh positive_control.py => Verification successful (exit 0)
  prepatch: bash scripts/nagini_verify.sh model_prepatch.py => Verification failed on is_pos_inf(Result()[0]) (exit 1)
  resolve:  run_resolve('scikit-learn__scikit-learn-26194', atk_4_faithful.patch) => RESOLVED True.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_4.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-26194.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A receiver-operating-characteristic computation finishes by prepending one
  extra leading entry to the descending sequence of decision thresholds, so the
  plotted curve is anchored at the origin (the leading entry corresponds to the
  degenerate operating point where no instance is predicted positive).

  The desired leading threshold is the POSITIVE-INFINITY sentinel: a single
  value that is correct regardless of the scale of the scores (which may be
  arbitrary decision values or probability estimates confined to the unit
  interval). The remaining thresholds are returned unchanged and in the same
  order.

So, given the finite descending thresholds `thresholds`, the result is the list
whose first element is the positive-infinity sentinel and whose remaining
elements are exactly `thresholds` in order.

The thresholds are modelled as a `List[float]` of interpreted real numbers
(verified with `--float-encoding=real`), since the distinguishing behaviour is
the real-number identity of the anchoring entry. Two unchanged numeric
primitives carry the infinity theory: `pos_inf` is the positive-infinity
sentinel and `is_pos_inf` tests whether a real number is that sentinel; their
provenance and executable soundness check are in mapping.md / axiom_check.py.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# axioms-start
@Pure
@ContractOnly
def is_pos_inf(x: float) -> bool:
    """Test whether a real number is the positive-infinity sentinel. An unchanged
    numeric primitive (the is-infinite test) the routine relies on; opaque
    predicate. Provenance + executable soundness check: mapping.md /
    axiom_check.py."""
    pass

@Pure
@ContractOnly
def pos_inf() -> float:
    """The positive-infinity sentinel. An unchanged numeric primitive the routine
    prepends as the anchoring threshold; it satisfies `is_pos_inf`. Provenance +
    executable soundness check: mapping.md / axiom_check.py."""
    Ensures(is_pos_inf(Result()))
# axioms-end

# pure-start
# (no pure helpers needed)
# pure-end

def anchor_thresholds(thresholds: List[float]) -> List[float]:
    # pre-conditions-start
    # The descending decision thresholds are the distinct finite scores; the
    # sequence is non-empty. Read-only input: fractional permission.
    Requires(Acc(list_pred(thresholds), 1 / 2))
    Requires(len(thresholds) >= 1)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(thresholds), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Exactly one extra leading entry is prepended.
    Ensures(len(Result()) == len(thresholds) + 1)
    # The leading anchoring threshold is the positive-infinity sentinel.
    Ensures(is_pos_inf(Result()[0]))
    # Every remaining threshold is returned unchanged, in the same order.
    Ensures(ToSeq(Result()).drop(1) == ToSeq(thresholds))
    # post-conditions-end
    # impl-start
    lead = pos_inf()
    result = [lead]  # type: List[float]
    i = 0
    while i < len(thresholds):
        # invariants-start
        Invariant(Acc(list_pred(thresholds), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(thresholds))
        Invariant(len(result) == i + 1)
        Invariant(ToSeq(result).take(1) == PSeq(lead))
        Invariant(is_pos_inf(ToSeq(result)[0]))
        Invariant(ToSeq(result).drop(1) == ToSeq(thresholds).take(i))
        # invariants-end
        result.append(thresholds[i])
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. FROZEN spec pins the output completely: len(Result())==len(thresholds)+1, is_pos_inf(Result()[0]) (the opaque predicate's ONLY known fact is pos_inf()'s Ensures(is_pos_inf(Result())), so Result()[0] must provably equal pos_inf()), and ToSeq(Result()).drop(1)==ToSeq(thresholds) (exact tail equality, in order). Thus any verifying same-spec impl must yield [pos_inf()]+thresholds, which refines to np.r_[np.inf, thresholds] = gold hunk.

Protocol executed Positive control (bundle model.py) verifies (10.2s, nagini_verify.sh exit 0). Prepatch reproduced: bundle model_prepatch.py (lead=thresholds[0]+1.0) FAILS on 'Postcondition ... Assertion is_pos_inf(Result()[0]) might not hold' (nagini_verify exit 1) — spec senses the change (G-DIFF).

7 distinct same-spec wrong impls built (impl-region-only edits; axioms/@Pure/Requires/Ensures byte-identical; confirmed SAME by `adversary same-spec` for all 7). Ran `adversary weakness nagini scikit-learn__scikit-learn-26194 <atk>` in parallel batches of <=3 (each spawns JVM+Z3):
  atk_1 prepatch-bug (finite thresholds[0]+1.0): same-spec, NOT verify (rejected — is_pos_inf fails).
  atk_2 boundary (no prepend; result=[]): same-spec, NOT verify (rejected — length/is_pos_inf fail).
  atk_3 control-flow-effect (correct anchor, tail appended twice): same-spec, NOT verify (rejected — length/tail fail).
  atk_4 ungrounded-oracle echo (lead=pos_inf() via temp, otherwise gold shape): same-spec AND VERIFIES (11.4s) => CANDIDATE.
  atk_5 control-flow-effect (correct anchor, tail copied in REVERSE): same-spec, NOT verify (rejected — tail!=thresholds).
  atk_6 boundary (correct prepend then extra trailing pos_inf(); len+1): same-spec, NOT verify (rejected — length/tail fail).
  atk_7 ungrounded oracle (lead=thresholds[0], finite, no pos_inf grounding): same-spec, NOT verify (rejected — is_pos_inf fails).

atk_4 is the ONLY CANDIDATE and is a semantic ECHO of the gold: it assigns lead=pos_inf() through a temp and does the identical forward copy, so its FAITHFUL refined patch is exactly the gold transform thresholds=np.r_[np.inf, thresholds]. Per protocol I MATERIALIZED that faithful patch (atk_4_faithful.patch) and RAN it through the official harness: run_resolve('scikit-learn__scikit-learn-26194', patch, timeout=1800) => RESOLVED: True, completed: True (Docker oracle, docker). A resolving same-spec echo is NOT a weakness (2026-08-06 G-PANEL-1/G-EQ policy: candidate breaks only if its refined patch does NOT resolve). No verifying wrong impl's faithful patch fails to resolve => verify=>correct holds.

refinement.md audit: A1=R (ndarray of float <-> List[float]; thresholds[k]<->thresholds[k], len<->len). A2=A-consumed (pos_inf <-> numpy.inf; proof consumes Ensures(is_pos_inf(Result())) to discharge anchoring post-condition; G-AX asserts np.isinf(np.inf), np.inf>0). A3=R+I (np.r_[x,arr] <-> [x]+list(arr); structural clauses len+1 and ToSeq(Result()).drop(1)==ToSeq(thresholds)). A4=A-consumed (is_pos_inf <-> numpy.isinf; the F2P discriminator np.isinf(thresholds[0])). No kind-3 (unexpressible-changed-op) steps: the one genuinely-changed operation (which scalar is prepended) is modeled DIRECTLY in the impl (lead=pos_inf()), not hidden behind an axiom of the function-under-change (roc_curve is NOT axiomatized). The two consumed axioms cover UNCHANGED numpy primitives (np.inf/np.isinf); their soundness/correspondence is audited by axiom_check.py against the real callees and real roc_curve. A-leg correspondence to real callees holds. Every leg is R / A-consumed / I.

Commands (project root; python=python; concurrent runs HOME env):
  same-spec: python -m swebench_unified.adversary same-spec nagini scikit-learn__scikit-learn-26194 atk_N.py (all 7 => SAME, exit 0)
  weakness:  python -m swebench_unified.adversary weakness  nagini scikit-learn__scikit-learn-26194 atk_N.py (atk_4 => CANDIDATE exit 0; atk_1,2,3,5,6,7 => NOT-A-COUNTEREXAMPLE/does-not-verify exit 2)
  positive control: bash scripts/nagini_verify.sh positive_control.py => Verification successful (exit 0)
  prepatch: bash scripts/nagini_verify.sh model_prepatch.py => Verification failed on is_pos_inf(Result()[0]) (exit 1)
  resolve:  run_resolve('scikit-learn__scikit-learn-26194', atk_4_faithful.patch) => RESOLVED True.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled anchor_thresholds spec and the real repo callee (the threshold-anchoring tail of roc_curve, sklearn/metrics/_ranking.py:1086, gold line `thresholds = np.r_[np.inf, thresholds]`).

Modeled spec pins Result = [pos_inf()] ++ thresholds via three postconditions: (1) len(Result())==len(thresholds)+1, (2) is_pos_inf(Result()[0]) (opaque @ContractOnly predicate whose only provable inhabitant is pos_inf()), (3) ToSeq(Result()).drop(1)==ToSeq(thresholds) (exact ordered tail). The real gold hunk `np.r_[np.inf, thresholds]` is a definitional identity with this step under the R-refinement ndarray<->List[float].

Checks performed:
- same-spec: exit 0 (spec region byte-identical to bundle).
- Real gold callee observed directly (HEAD=base carries gold `thresholds = np.r_[np.inf, thresholds]` at _ranking.py:1086). Ran real roc_curve on probability estimates, ties, all-equal scores, large-magnitude (1e9), negative/confidence scores >1, singleton-distinct: EVERY case yields leading=+inf (is_pos_inf, >0), tail = original finite thresholds unchanged & in order, length=n+1 — exactly the three postconditions. No divergence.
- Precondition len>=1 excludes no real input (roc_curve requires both classes present so _binary_clf_curve/drop_intermediate always yield >=1 threshold); descending order left unconstrained, matching mapping.md — spec is not too strong.
- Axioms pos_inf/is_pos_inf model version-independent IEEE-754 primitives np.inf/np.isinf; is_pos_inf deliberately under-constrained on finite reals (no over-approximation).
- G-DIFF sanity: model_prepatch.py (lead=thresholds[0]+1.0, finite) FAILS is_pos_inf(Result()[0]) — spec discriminates the change without being stronger than real post-patch behavior.

Could not construct a diverging input. Spec is FAITHFUL to the real repo behavior; the recorded Role-3 pass is upheld.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** panel_3: leakage accepted per RELAXED_LEAKAGE.md (agent flagged: leakage)

**What the spec view discloses.** Quoted from this bundle's own `RELAXED_LEAKAGE.md`, its opening summary:

> The discriminating vocabulary of the gold fix (`np.inf` / `np.isinf` / "infinite leading threshold") appears ONLY in the gold patch and the hidden `test_patch`, never in the solver-visible `problem_statement` (and not in `hints_text` either). Any FAITHFUL spec must pin the infinite leading element (else the prepatch would not fail — G-DIFF, and a "clip to <= 1" impl would wrongly verify), but no spec derivable from the `problem_statement` alone can name `np.inf`, because the public issue is about *clipping down to 1* and never about an infinite sentinel.

**Why the disclosure is accepted.** The same file's account of why the disclosure is forced rather than avoidable, "Why this is not a de-narration fix (the leak is the behavior, not narration)":

> The mechanical G-LEAK screen also passes (no diff line, no patched path `sklearn/metrics/_ranking.py`, no patched symbol `roc_curve`/`np.r_`, no `+1` rule, no bug->fix narration; the spec view describes the abstract behavior "anchor the ROC curve at the origin with a positive-infinity leading threshold"). The relaxation is needed because the **semantic** discriminator the spec must pin to be faithful — that the leading threshold is `+inf` — is itself absent from the public issue and present only in the gold/`test_patch`.

**What this role measured.** The disposition this role defers to is recorded rather than assumed: `meta.json` sets `relaxed_leakage: true`, the bundle ships the `RELAXED_LEAKAGE.md` quoted above, and `G-LEAK` records `relaxed` with the detail `semantic leak of gold discriminator; unavoidable for a faithful spec`. The file quoted here is byte-identical to the one that gate read (sha256 `941606fd97fc`, recorded under `G-LEAK`'s own sources), and it carries no instruction to the role reviewing it -- a relaxation document that told this panel which verdict to submit would make `G-LEAK` record a failure instead of a relaxation, so the argument above is one this role judged rather than one it was handed.

`G-LEAK`'s lexical screen recorded no failures of its own, which is what places this disclosure in what the specification pins rather than in a word the spec view uses. This role is advisory and only `G-LEAK` is recorded for leakage on this cell, which is why the deferral is a pass here and not a status of its own. The panel submitted `LEAKAGE`; a non-empty verdict is required for the deferral to apply at all, so a review that never ran is recorded as reaching no verdict rather than as deferring to this file. The panel's own account -- whether it accepts the argument quoted above or presses further against it -- is published in this cell's audit record.

Counterexample / evidence:

```
Token check over the solver-visible problem_statement (case-insensitive): `inf`/`isinf`/`np.inf` are ABSENT, while `clip`/`above 1`/`+ 1` are PRESENT. The PS frames the defect as 'roc_curve returns a threshold > 1 for probability estimates' and proposes the OPPOSITE fix ('check thresholds.max() <= 1 ... clip thresholds to not be above 1'), even shipping a candidate test asserting `np.logical_or(thresholds <= 1, thresholds >= 0).all()` (never mentions infinity). The gold instead prepends `np.inf` (an INFINITE leading threshold) and the committed F2P test asserts `np.isinf(thresholds[0])`. The spec view's positive-infinity discriminator (`pos_inf`/`is_pos_inf`, post-condition `is_pos_inf(Result()[0])`) is therefore reconstructable ONLY from the gold patch + hidden test_patch, not from the public problem_statement (nor hints_text). A problem_statement-only solver would reach for clip/min, never `np.inf`. This lets a solver reproduce the gold's concrete discriminator that the public issue does not reveal.
```

G-PANEL-3 attacker verdict is LEAKAGE. However this is a documented, ACCEPTED relaxed-leakage bundle (RELAXED_LEAKAGE.md, project decision 2026-06-14; RELAXED_LEAKAGE.md honored by leak.py condition gates). It is a genuine problem_statement<->gold MISMATCH: any FAITHFUL spec must pin the +inf leading element (else prepatch would not fail G-DIFF and a 'clip to <=1' impl would wrongly verify), yet no PS-derivable (clip-down) spec can name np.inf — faithful+non-leaking is provably impossible here. Per the 2026-08-06/07 policy (G-PANEL-3 defers to accepted RELAXED_LEAKAGE.md), on a relaxed bundle a LEAKAGE verdict records pass+note, never fail; recorded as 'pass'. same_spec confirmed byte-identical spec regions between model.py and model_prepatch.py; the mechanical/lexical G-LEAK screen passes (no diff lines/paths/patched-symbol/+1-narration) — the leak is semantic, not lexical. Soundness axes are intact (G-VERIFY/G-DIFF/G-AX/G-CONF/G-RESOLVE all pass); this is a no-leakage relaxation, not a soundness defect.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded LEAKAGE. The record is a pass because the disclosure it names had already been accepted by a reviewer: an accepted relaxation is the leakage GATE's disposition to record, and this cell records G-LEAK as `relaxed`. This role defers to that disposition rather than re-failing the cell, and is recorded as a pass with a note because `relaxed` is not a status it may take. So the pass rests on an accepted disclosure and not on the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `RELAXED_LEAKAGE.md`, which ships in this bundle, so a reader can start there.