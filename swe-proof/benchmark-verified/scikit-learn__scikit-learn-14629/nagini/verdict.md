# P2 adversarial audit — scikit-learn__scikit-learn-14629

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk5.py`, `atk6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Estimator:
@@ -81,7 +80,6 @@
     Requires(Acc(list_pred(estimators), 1 / 2))
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
         Acc(estimators[k].cls_vals, 1 / 4)))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The input list is left exactly as it was (returned at the same fractional
@@ -101,20 +99,5 @@
     # post-conditions-end
     # impl-start
     result = []  # type: List[PSeq[int]]
-    i = 0
-    while i < len(estimators):
-        # invariants-start
-        Invariant(Acc(list_pred(estimators), 1 / 2))
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
-            Acc(estimators[k].cls_vals, 1 / 4)))))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(estimators))
-        Invariant(len(result) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == est_vals(estimators[k])))))
-        Invariant(MustTerminate(len(estimators) - i + 1))
-        # invariants-end
-        result.append(est_vals(estimators[i]))
-        i = i + 1
     return result
     # impl-end
```

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Estimator:
@@ -81,7 +80,6 @@
     Requires(Acc(list_pred(estimators), 1 / 2))
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
         Acc(estimators[k].cls_vals, 1 / 4)))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The input list is left exactly as it was (returned at the same fractional
@@ -102,18 +100,17 @@
     # impl-start
     result = []  # type: List[PSeq[int]]
     i = 0
-    while i < len(estimators):
-        # invariants-start
+    n = len(estimators) - 1
+    while i < n:
         Invariant(Acc(list_pred(estimators), 1 / 2))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
             Acc(estimators[k].cls_vals, 1 / 4)))))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(estimators))
+        Invariant(0 <= i and i <= n)
+        Invariant(n == len(estimators) - 1)
         Invariant(len(result) == i)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
             result[k] == est_vals(estimators[k])))))
-        Invariant(MustTerminate(len(estimators) - i + 1))
-        # invariants-end
         result.append(est_vals(estimators[i]))
         i = i + 1
     return result
```

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Estimator:
@@ -81,7 +80,6 @@
     Requires(Acc(list_pred(estimators), 1 / 2))
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
         Acc(estimators[k].cls_vals, 1 / 4)))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The input list is left exactly as it was (returned at the same fractional
@@ -103,7 +101,6 @@
     result = []  # type: List[PSeq[int]]
     i = 0
     while i < len(estimators):
-        # invariants-start
         Invariant(Acc(list_pred(estimators), 1 / 2))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
             Acc(estimators[k].cls_vals, 1 / 4)))))
@@ -111,10 +108,8 @@
         Invariant(0 <= i and i <= len(estimators))
         Invariant(len(result) == i)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == est_vals(estimators[k])))))
-        Invariant(MustTerminate(len(estimators) - i + 1))
-        # invariants-end
-        result.append(est_vals(estimators[i]))
+            result[k] == est_vals(estimators[len(estimators) - 1 - k])))))
+        result.append(est_vals(estimators[len(estimators) - 1 - i]))
         i = i + 1
     return result
     # impl-end
```

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Estimator:
@@ -81,7 +80,6 @@
     Requires(Acc(list_pred(estimators), 1 / 2))
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
         Acc(estimators[k].cls_vals, 1 / 4)))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The input list is left exactly as it was (returned at the same fractional
@@ -103,7 +101,6 @@
     result = []  # type: List[PSeq[int]]
     i = 0
     while i < len(estimators):
-        # invariants-start
         Invariant(Acc(list_pred(estimators), 1 / 2))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
             Acc(estimators[k].cls_vals, 1 / 4)))))
@@ -111,10 +108,8 @@
         Invariant(0 <= i and i <= len(estimators))
         Invariant(len(result) == i)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == est_vals(estimators[k])))))
-        Invariant(MustTerminate(len(estimators) - i + 1))
-        # invariants-end
-        result.append(est_vals(estimators[i]))
+            result[k] == est_vals(estimators[0])))))
+        result.append(est_vals(estimators[0]))
         i = i + 1
     return result
     # impl-end
```

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Estimator:
@@ -81,7 +80,6 @@
     Requires(Acc(list_pred(estimators), 1 / 2))
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
         Acc(estimators[k].cls_vals, 1 / 4)))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The input list is left exactly as it was (returned at the same fractional
@@ -102,19 +100,21 @@
     # impl-start
     result = []  # type: List[PSeq[int]]
     i = 0
-    while i < len(estimators):
-        # invariants-start
+    n = len(estimators)
+    while i < n:
         Invariant(Acc(list_pred(estimators), 1 / 2))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
             Acc(estimators[k].cls_vals, 1 / 4)))))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(estimators))
+        Invariant(0 <= i and i <= n)
+        Invariant(n == len(estimators))
         Invariant(len(result) == i)
-        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
-            result[k] == est_vals(estimators[k])))))
-        Invariant(MustTerminate(len(estimators) - i + 1))
-        # invariants-end
-        result.append(est_vals(estimators[i]))
+        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i and k + 1 < n,
+            result[k] == est_vals(estimators[k + 1])))))
+        if i + 1 < n:
+            result.append(est_vals(estimators[i + 1]))
+        else:
+            result.append(est_vals(estimators[0]))
         i = i + 1
     return result
     # impl-end
```

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Estimator:
@@ -81,7 +80,6 @@
     Requires(Acc(list_pred(estimators), 1 / 2))
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
         Acc(estimators[k].cls_vals, 1 / 4)))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The input list is left exactly as it was (returned at the same fractional
@@ -103,7 +101,6 @@
     result = []  # type: List[PSeq[int]]
     i = 0
     while i < len(estimators):
-        # invariants-start
         Invariant(Acc(list_pred(estimators), 1 / 2))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
             Acc(estimators[k].cls_vals, 1 / 4)))))
@@ -112,9 +109,9 @@
         Invariant(len(result) == i)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
             result[k] == est_vals(estimators[k])))))
-        Invariant(MustTerminate(len(estimators) - i + 1))
-        # invariants-end
         result.append(est_vals(estimators[i]))
         i = i + 1
+    if len(estimators) > 0:
+        result.append(est_vals(estimators[0]))
     return result
     # impl-end
```

Attack 7 — `atk7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -39,7 +39,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 class Estimator:
@@ -81,7 +80,6 @@
     Requires(Acc(list_pred(estimators), 1 / 2))
     Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
         Acc(estimators[k].cls_vals, 1 / 4)))))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The input list is left exactly as it was (returned at the same fractional
@@ -103,7 +101,6 @@
     result = []  # type: List[PSeq[int]]
     i = 0
     while i < len(estimators):
-        # invariants-start
         Invariant(Acc(list_pred(estimators), 1 / 2))
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
             Acc(estimators[k].cls_vals, 1 / 4)))))
@@ -112,9 +109,9 @@
         Invariant(len(result) == i)
         Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
             result[k] == est_vals(estimators[k])))))
-        Invariant(MustTerminate(len(estimators) - i + 1))
-        # invariants-end
-        result.append(est_vals(estimators[i]))
+        e = estimators[i]  # type: Estimator
+        v = est_vals(e)  # type: PSeq[int]
+        result.append(v)
         i = i + 1
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-14629.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A multi-output classifier wraps one fitted single-output sub-classifier per
  target column. After fitting, the wrapper must expose the per-output class
  labels as an ordered collection — one entry per sub-classifier, in the same
  order as the sub-classifiers, each entry carrying exactly the class labels
  that the corresponding sub-classifier learned.

  The desired guarantee is therefore that this collection:

    (1) has exactly as many entries as there are fitted sub-classifiers (one
        per output), and

    (2) at every position holds the class labels of the sub-classifier at that
        position — element-for-element the same labels: position ``i`` carries
        the labels of sub-classifier ``i`` (not a reordering, not a subset, not
        a constant, not the labels of a different output).

  A wrapper that leaves this collection unpopulated (so an output position has
  no class labels at all) is exactly the defect this specification forbids: a
  consumer that walks the per-output class labels must find, at each position,
  the labels of the corresponding sub-classifier.

The fitted sub-classifiers are modelled as a read-only ``List[Estimator]``,
each ``Estimator`` exposing only the touched facet — the class labels it learned
for its output, modelled as a pure label-sequence value (``PSeq[int]``, the
sequence of class-label codes; element values are the discriminator, matching
how a consumer compares the per-output labels). The produced collection is a
``List[PSeq[int]]``; the per-position guarantee is element-wise value equality
between ``Result()[i]`` and the labels of sub-classifier ``i`` — pinning each
entry to the genuine per-output labels rather than to a constant, a reordering,
or another output's labels.

No callee is axiomatized: the gathering is pure per-element structural logic,
modelled deeply. Markers (machine-parsed) delimit the spec / proof / impl
regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Estimator:
    """One fitted single-output sub-classifier, exposing only the touched
    facet: ``cls_vals``, the sequence of class-label codes it learned for its
    output (read-only here). Its element values are the discriminator: a
    consumer compares the per-output labels element-for-element."""

    def __init__(self, cls_vals: PSeq[int]) -> None:
        Ensures(Acc(self.cls_vals) and self.cls_vals == cls_vals)  # type: ignore
        self.cls_vals = cls_vals  # type: PSeq[int]


# axioms-start
# (No consumed axioms. The added behaviour — gathering each fitted
# sub-classifier's class labels into one ordered per-output collection — is
# pure per-element structural logic, modelled DEEPLY by the verified loop below.
# The unchanged fitting step that produces the sub-classifiers is not re-derived:
# the already-fitted list is taken as input, so no callee is axiomatized.)
# axioms-end


# pure-start
@Pure
def est_vals(e: Estimator) -> PSeq[int]:
    """The class labels of one fitted sub-classifier, as a pure label-sequence
    value — the per-output labels position ``i`` of the produced collection must
    carry. Reads the touched facet at a fractional permission (read-only)."""
    Requires(Acc(e.cls_vals, 1 / 4))
    return e.cls_vals
# pure-end


def gather_output_classes(estimators: List[Estimator]) -> List[PSeq[int]]:
    # pre-conditions-start
    # The fitted sub-classifier list is READ-ONLY here (the gathering iterates
    # over it without mutating it): its spine and each sub-classifier's touched
    # facet are required at fractional permission (directive 5).
    Requires(Acc(list_pred(estimators), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
        Acc(estimators[k].cls_vals, 1 / 4)))))
    # pre-conditions-end
    # post-conditions-start
    # The input list is left exactly as it was (returned at the same fractional
    # permission), so the operation cannot satisfy the spec by mutating it.
    Ensures(Acc(list_pred(estimators), 1 / 2))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
        Acc(estimators[k].cls_vals, 1 / 4)))))
    Ensures(Acc(list_pred(Result())))
    # (1) one entry per fitted sub-classifier.
    Ensures(len(Result()) == len(estimators))
    # (2) position i carries exactly the class labels of sub-classifier i —
    # element-for-element value equality (the property a consumer of the
    # per-output labels observes): not a reordering, not a subset, not a
    # constant, not another output's labels.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
        Result()[k] == est_vals(estimators[k])))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[PSeq[int]]
    i = 0
    while i < len(estimators):
        # invariants-start
        Invariant(Acc(list_pred(estimators), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
            Acc(estimators[k].cls_vals, 1 / 4)))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(estimators))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == est_vals(estimators[k])))))
        # invariants-end
        result.append(est_vals(estimators[i]))
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of scikit-learn__scikit-learn-14629 (nagini). Scratch dir All attacks copy model.py with ONLY the impl region edited (spec/@Pure/Requires/Ensures/Invariant byte-identical; confirmed same spec prefix for all 8 files).

A-LEG / DEEP-MODEL AUDIT: refinement.md and mapping.md declare NO consumed axioms and NO A-references — the per-output gathering is modeled DEEPLY (verified index loop appending est_vals(estimators[i])), and the unchanged super().fit is taken as a typed List[Estimator] input (tag I), not axiomatized. Confirmed in model.py: axioms region empty; est_vals is @Pure reading the field at 1/4 permission; there is no @ContractOnly callee. Hence there is no opaque-callee correspondence that could be unfaithful and no kind-3 leg. axiom_check.py validates the behavioural claim directly against the real patched code (G-AX pass, 45 cases). Every refinement.md leg is R / I / cosmetic-I — audit passes.

### ATTACKS (each run: `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-14629 <path>`):
- atk1.py PREPATCH BUG (return [] unpopulated): NOT-A-COUNTEREXAMPLE, verification failed (exit 2). Reproduces the prepatch defect the spec forbids -> prepatch_reproduced=true.
- atk2.py drop-last (while i<len-1, wrong length): verification failed (exit 2).
- atk3.py reversed order (position i = estimators[len-1-i]): verification failed (exit 2).
- atk4.py constant (every entry = estimators[0]): verification failed (exit 2).
- atk5.py shifted-by-one (position i = estimators[i+1], last wraps to 0): verification failed (exit 2).
- atk6.py duplicate-last (correct loop + one extra append, wrong length): verification failed (exit 2).
- atk7.py VALUE-EQUAL alternate construction (bind e=estimators[i]; v=est_vals(e); append v): CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 11.7s, exit 0).
All six wrong impls (partial-domain/length, boundary, control-flow-effect reorderings, constant/ungrounded echo) are correctly REJECTED by the postconditions len(Result())==len(estimators) + Forall k Result()[k]==est_vals(estimators[k]) + frame preservation (impl holds only 1/4, cannot mutate).

RESOLVE RUNS (official harness, swebench_unified.harness.run_resolve, timeout 1800, one at a time under docker) for EVERY verifying candidate:
- pos_control.py (gold-faithful; faithful patch = gold verbatim): resolved=True completed=True note=resolved.
- atk7.py (faithful patch = explicit index-loop form of the comprehension, behaviourally identical/value-equal/same order): FIRST attempt returned completed=False 'no report' due to a stale hunk-header count (+325,28 vs actual 32 added lines); corrected header to +325,32 (line accounting re-validated for both hunks), RE-RAN -> resolved=True completed=True note=resolved.
Both verifying candidates' materialized faithful patches RESOLVE. No verify-but-not-resolve witness exists.

VERDICT: SOUND. >=5 distinct attacks run (6 rejected + 1 benign candidate + positive control), the prepatch bug reproduced, the A-legs verified (there are none to be unfaithful), and every verifying impl's faithful refined patch resolves under the official harness. The spec is neither too weak (all wrong impls rejected) nor too strong (value-equal fix admitted and resolves).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk5.py`, `atk6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-14629.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A multi-output classifier wraps one fitted single-output sub-classifier per
  target column. After fitting, the wrapper must expose the per-output class
  labels as an ordered collection — one entry per sub-classifier, in the same
  order as the sub-classifiers, each entry carrying exactly the class labels
  that the corresponding sub-classifier learned.

  The desired guarantee is therefore that this collection:

    (1) has exactly as many entries as there are fitted sub-classifiers (one
        per output), and

    (2) at every position holds the class labels of the sub-classifier at that
        position — element-for-element the same labels: position ``i`` carries
        the labels of sub-classifier ``i`` (not a reordering, not a subset, not
        a constant, not the labels of a different output).

  A wrapper that leaves this collection unpopulated (so an output position has
  no class labels at all) is exactly the defect this specification forbids: a
  consumer that walks the per-output class labels must find, at each position,
  the labels of the corresponding sub-classifier.

The fitted sub-classifiers are modelled as a read-only ``List[Estimator]``,
each ``Estimator`` exposing only the touched facet — the class labels it learned
for its output, modelled as a pure label-sequence value (``PSeq[int]``, the
sequence of class-label codes; element values are the discriminator, matching
how a consumer compares the per-output labels). The produced collection is a
``List[PSeq[int]]``; the per-position guarantee is element-wise value equality
between ``Result()[i]`` and the labels of sub-classifier ``i`` — pinning each
entry to the genuine per-output labels rather than to a constant, a reordering,
or another output's labels.

No callee is axiomatized: the gathering is pure per-element structural logic,
modelled deeply. Markers (machine-parsed) delimit the spec / proof / impl
regions.
"""
from typing import List
from nagini_contracts.contracts import *


class Estimator:
    """One fitted single-output sub-classifier, exposing only the touched
    facet: ``cls_vals``, the sequence of class-label codes it learned for its
    output (read-only here). Its element values are the discriminator: a
    consumer compares the per-output labels element-for-element."""

    def __init__(self, cls_vals: PSeq[int]) -> None:
        Ensures(Acc(self.cls_vals) and self.cls_vals == cls_vals)  # type: ignore
        self.cls_vals = cls_vals  # type: PSeq[int]


# axioms-start
# (No consumed axioms. The added behaviour — gathering each fitted
# sub-classifier's class labels into one ordered per-output collection — is
# pure per-element structural logic, modelled DEEPLY by the verified loop below.
# The unchanged fitting step that produces the sub-classifiers is not re-derived:
# the already-fitted list is taken as input, so no callee is axiomatized.)
# axioms-end


# pure-start
@Pure
def est_vals(e: Estimator) -> PSeq[int]:
    """The class labels of one fitted sub-classifier, as a pure label-sequence
    value — the per-output labels position ``i`` of the produced collection must
    carry. Reads the touched facet at a fractional permission (read-only)."""
    Requires(Acc(e.cls_vals, 1 / 4))
    return e.cls_vals
# pure-end


def gather_output_classes(estimators: List[Estimator]) -> List[PSeq[int]]:
    # pre-conditions-start
    # The fitted sub-classifier list is READ-ONLY here (the gathering iterates
    # over it without mutating it): its spine and each sub-classifier's touched
    # facet are required at fractional permission (directive 5).
    Requires(Acc(list_pred(estimators), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
        Acc(estimators[k].cls_vals, 1 / 4)))))
    # pre-conditions-end
    # post-conditions-start
    # The input list is left exactly as it was (returned at the same fractional
    # permission), so the operation cannot satisfy the spec by mutating it.
    Ensures(Acc(list_pred(estimators), 1 / 2))
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
        Acc(estimators[k].cls_vals, 1 / 4)))))
    Ensures(Acc(list_pred(Result())))
    # (1) one entry per fitted sub-classifier.
    Ensures(len(Result()) == len(estimators))
    # (2) position i carries exactly the class labels of sub-classifier i —
    # element-for-element value equality (the property a consumer of the
    # per-output labels observes): not a reordering, not a subset, not a
    # constant, not another output's labels.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
        Result()[k] == est_vals(estimators[k])))))
    # post-conditions-end
    # impl-start
    result = []  # type: List[PSeq[int]]
    i = 0
    while i < len(estimators):
        # invariants-start
        Invariant(Acc(list_pred(estimators), 1 / 2))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(estimators),
            Acc(estimators[k].cls_vals, 1 / 4)))))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(estimators))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
            result[k] == est_vals(estimators[k])))))
        # invariants-end
        result.append(est_vals(estimators[i]))
        i = i + 1
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of scikit-learn__scikit-learn-14629 (nagini). Scratch dir All attacks copy model.py with ONLY the impl region edited (spec/@Pure/Requires/Ensures/Invariant byte-identical; confirmed same spec prefix for all 8 files).

A-LEG / DEEP-MODEL AUDIT: refinement.md and mapping.md declare NO consumed axioms and NO A-references — the per-output gathering is modeled DEEPLY (verified index loop appending est_vals(estimators[i])), and the unchanged super().fit is taken as a typed List[Estimator] input (tag I), not axiomatized. Confirmed in model.py: axioms region empty; est_vals is @Pure reading the field at 1/4 permission; there is no @ContractOnly callee. Hence there is no opaque-callee correspondence that could be unfaithful and no kind-3 leg. axiom_check.py validates the behavioural claim directly against the real patched code (G-AX pass, 45 cases). Every refinement.md leg is R / I / cosmetic-I — audit passes.

### ATTACKS (each run: `python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-14629 <path>`):
- atk1.py PREPATCH BUG (return [] unpopulated): NOT-A-COUNTEREXAMPLE, verification failed (exit 2). Reproduces the prepatch defect the spec forbids -> prepatch_reproduced=true.
- atk2.py drop-last (while i<len-1, wrong length): verification failed (exit 2).
- atk3.py reversed order (position i = estimators[len-1-i]): verification failed (exit 2).
- atk4.py constant (every entry = estimators[0]): verification failed (exit 2).
- atk5.py shifted-by-one (position i = estimators[i+1], last wraps to 0): verification failed (exit 2).
- atk6.py duplicate-last (correct loop + one extra append, wrong length): verification failed (exit 2).
- atk7.py VALUE-EQUAL alternate construction (bind e=estimators[i]; v=est_vals(e); append v): CANDIDATE-COUNTEREXAMPLE (shares spec AND verifies, 11.7s, exit 0).
All six wrong impls (partial-domain/length, boundary, control-flow-effect reorderings, constant/ungrounded echo) are correctly REJECTED by the postconditions len(Result())==len(estimators) + Forall k Result()[k]==est_vals(estimators[k]) + frame preservation (impl holds only 1/4, cannot mutate).

RESOLVE RUNS (official harness, swebench_unified.harness.run_resolve, timeout 1800, one at a time under docker) for EVERY verifying candidate:
- pos_control.py (gold-faithful; faithful patch = gold verbatim): resolved=True completed=True note=resolved.
- atk7.py (faithful patch = explicit index-loop form of the comprehension, behaviourally identical/value-equal/same order): FIRST attempt returned completed=False 'no report' due to a stale hunk-header count (+325,28 vs actual 32 added lines); corrected header to +325,32 (line accounting re-validated for both hunks), RE-RAN -> resolved=True completed=True note=resolved.
Both verifying candidates' materialized faithful patches RESOLVE. No verify-but-not-resolve witness exists.

VERDICT: SOUND. >=5 distinct attacks run (6 rejected + 1 benign candidate + positive control), the prepatch bug reproduced, the A-legs verified (there are none to be unfaithful), and every verifying impl's faithful refined patch resolves under the official harness. The spec is neither too weak (all wrong impls rejected) nor too strong (value-equal fix admitted and resolves).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical to the bundle (same-spec command returns SAME, exit 0). Faithfulness assessed against the real repo callee: the gold patch (base_commit 4aded39b56, verified — base has NO fit override on MultiOutputClassifier, patch adds `self.classes_ = [estimator.classes_ for estimator in self.estimators_]` then `return self`). The modeled `gather_output_classes` pins exactly two postconditions plus read-only frame preservation: (1) len(Result()) == len(estimators); (2) Forall k: Result()[k] == est_vals(estimators[k]) — element-wise VALUE equality (PSeq[int]), NOT object identity.

Checked each postcondition against the real callee's output for arbitrary fitted inputs:
- (1) The list comprehension always yields exactly one entry per fitted sub-estimator, in index order → holds for every input (any n_outputs >= 0, including 0).
- (2) classes_[i] IS estimators_[i].classes_ (same array object), which is trivially value-equal to itself → the VALUE-equality postcondition holds for every input. Because the spec pins VALUE (not identity), it is strictly WEAKER than what the gold produces (references); a value-equal copy fix would also satisfy it. A too-strong identity pin would be the classic over-strong defect, and the model explicitly avoids it (mapping.md §2, refinement.md A4/A5).
- Ordering: index walk i=0..len-1 mirrors `for estimator in self.estimators_` iteration order → position i carries output i's labels, matching reality.
- Frame: the input list and each cls_vals facet are returned at the same fractional permission — the gathering does not mutate estimators_, matching the read-only comprehension.

There is NO input where the modeled function's postconditions disagree with (demand more than) the real patched fit's output. The spec is the weakest property the F2P test (assert_array_equal, a value comparison) and cited consumer (_enforce_prediction_order) discriminate on. No callee is axiomatized (gathering modeled deeply), so no axiom-unfaithfulness surface exists. Corroborated by G-AX/axiom_check.py exercising the real patched code in-container. Spec is not too strong and does not drift from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True): no diff markers, no gold-patch line reproduced (impl region elided to `...`), no patched file path `sklearn/multioutput.py` or dotted module path, and no spec-view identifier/comment echoes a patched repo symbol outside the problem statement.

Gold edit: add `self.classes_ = [estimator.classes_ for estimator in self.estimators_]` to `MultiOutputClassifier.fit` (+ a cosmetic whitespace dedent of `raise ValueError("invalid order")` in `_BaseChain.fit`, not modeled).

Semantic check against the PUBLIC problem_statement only (not hints_text): the problem statement already discloses the entire discriminating content of the fix — it states the AttributeError is that `MultiOutputClassifier` has no `classes_`, and explicitly says "To obtain the `classes_` attribute of a `MultiOutputClassifier`, you need `mo_clf.estimators_[i].classes_` instead." So the desired behaviour (populate a per-output collection where entry i carries sub-estimator i's class labels) is public in the task itself.

The spec view abstracts every repo symbol: `classes_`->`Result()`/`cls_vals`, `estimators_`->`estimators`, `MultiOutputClassifier.fit`->`gather_output_classes`, sub-estimator->`Estimator`. Prose is framed as desired behaviour, not an edit; no bug/fix narration terms; the cosmetic second hunk is entirely absent. Nothing in the spec view reveals the gold edit beyond what the public problem_statement already states. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
