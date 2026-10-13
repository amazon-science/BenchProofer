# P2 adversarial audit — scikit-learn__scikit-learn-13439

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -22,7 +22,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -41,7 +40,6 @@
     # The stage collection is read-only: the size query never mutates it, so it
     # is required AND ensured at fractional permission (directive 5).
     Requires(Acc(list_pred(steps), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(steps), 1 / 2))
@@ -51,5 +49,5 @@
     Ensures(Result() == len(steps))
     # post-conditions-end
     # impl-start
-    return len(steps)
+    return len(steps) - 1
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -22,7 +22,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -41,7 +40,6 @@
     # The stage collection is read-only: the size query never mutates it, so it
     # is required AND ensured at fractional permission (directive 5).
     Requires(Acc(list_pred(steps), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(steps), 1 / 2))
@@ -51,5 +49,5 @@
     Ensures(Result() == len(steps))
     # post-conditions-end
     # impl-start
-    return len(steps)
+    return len(steps) + 1
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -22,7 +22,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -41,7 +40,6 @@
     # The stage collection is read-only: the size query never mutates it, so it
     # is required AND ensured at fractional permission (directive 5).
     Requires(Acc(list_pred(steps), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(steps), 1 / 2))
@@ -51,5 +49,5 @@
     Ensures(Result() == len(steps))
     # post-conditions-end
     # impl-start
-    return len(steps)
+    return 0
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -22,7 +22,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -41,7 +40,6 @@
     # The stage collection is read-only: the size query never mutates it, so it
     # is required AND ensured at fractional permission (directive 5).
     Requires(Acc(list_pred(steps), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(steps), 1 / 2))
@@ -51,5 +49,7 @@
     Ensures(Result() == len(steps))
     # post-conditions-end
     # impl-start
+    if len(steps) == 0:
+        return 1
     return len(steps)
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -22,7 +22,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -41,7 +40,6 @@
     # The stage collection is read-only: the size query never mutates it, so it
     # is required AND ensured at fractional permission (directive 5).
     Requires(Acc(list_pred(steps), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(steps), 1 / 2))
@@ -51,5 +49,5 @@
     Ensures(Result() == len(steps))
     # post-conditions-end
     # impl-start
-    return len(steps)
+    return len(steps) * 2
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -22,7 +22,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -41,7 +40,6 @@
     # The stage collection is read-only: the size query never mutates it, so it
     # is required AND ensured at fractional permission (directive 5).
     Requires(Acc(list_pred(steps), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(steps), 1 / 2))
@@ -51,5 +49,6 @@
     Ensures(Result() == len(steps))
     # post-conditions-end
     # impl-start
+    steps.append(0)
     return len(steps)
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -22,7 +22,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -41,7 +40,6 @@
     # The stage collection is read-only: the size query never mutates it, so it
     # is required AND ensured at fractional permission (directive 5).
     Requires(Acc(list_pred(steps), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(steps), 1 / 2))
@@ -51,5 +49,5 @@
     Ensures(Result() == len(steps))
     # post-conditions-end
     # impl-start
-    return len(steps)
+    return 2
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-13439.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A composite estimator is built as an ORDERED collection of constituent
  stages. Client code that indexes the composite with an integer- or
  slice-based handle relies on the collection reporting its SIZE: a query for
  "how many stages does this composite hold?" must return the exact number of
  stages it was constructed from — every stage counted once, including the
  final stage and any inert placeholder stages, none omitted and none counted
  twice. The size is therefore the cardinality of the stage collection itself,
  so that an index handle spanning "from the start up to the size" covers the
  whole collection.

The stage collection is modelled as `List[int]`, one element per stage (the
element values — the (name, estimator) pairs — are irrelevant; only the
cardinality is observed). The reported size is an `int` equal to the length of
that collection. No callee is axiomatized: the behaviour is the length of the
input collection, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No axiomatized callees: the reported size is the length of the input
#  collection, modelled deeply.)
# axioms-end


# pure-start
# (No pure helpers needed.)
# pure-end


def composite_size(steps: List[int]) -> int:
    # pre-conditions-start
    # The stage collection is read-only: the size query never mutates it, so it
    # is required AND ensured at fractional permission (directive 5).
    Requires(Acc(list_pred(steps), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(steps), 1 / 2))
    # The reported size is exactly the cardinality of the stage collection:
    # every stage counted once (final stage and inert placeholders included),
    # none omitted. Grounded in the actual input collection.
    Ensures(Result() == len(steps))
    # post-conditions-end
    # impl-start
    return len(steps)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec: composite_size(steps: List[int]) -> int with Requires/Ensures Acc(list_pred(steps),1/2) (read-only, required AND ensured) and Ensures(Result() == len(steps)). This postcondition pins the return value EXACTLY for every input, and the fractional-permission-preserved-not-full contract blocks any impl from satisfying the spec by mutating steps. axioms region is genuinely empty (comment-only) — no @ContractOnly callee, no @Pure helper, no A-consumed/A-reference leg, no deep model standing in for a real callee, so G-AX is vacuous and there is nothing to falsify on the A-legs.

Battery (all copied from model.py, ONLY impl region edited; axioms/@Pure/Requires/Ensures byte-identical; same-spec spot-checked SAME on atk_1 and atk_6):
  atk_1 = return len(steps)-1  (PREPATCH bug: terminal-stage-dropping under-count, mirrors _iter(with_final=False))
  atk_2 = return len(steps)+1  (off-by-one high)
  atk_3 = return 0            (constant/ungrounded)
  atk_4 = 1 on empty else len (partial-domain, boundary N==0)
  atk_5 = return len(steps)*2 (scaling/double-count)
  atk_6 = steps.append(0); return len(steps) (control-flow-effect: mutation of read-only list)
  atk_7 = return 2            (ungrounded-oracle echo of the F2P 2-step answer)

Command per attack: python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-13439 atk_N.py (run concurrently in 3 batches, ≤3 JVMs).
Results: ALL SEVEN returned exit 2 = NOT-A-COUNTEREXAMPLE ('attack does not verify (verification failed) — the spec rejected this impl'). atk_6 fails precisely because the read-only 1/2 permission (Ensures Acc(...,1/2)) forbids append. Positive control (verbatim model impl 'return len(steps)') verifies: bash scripts/nagini_verify.sh pos_control.py -> exit 0, 'Verification successful' (12.0s).

Since NO attack is a CANDIDATE (none shares-spec-AND-verifies), there is no verifying wrong impl and thus no faithful refined patch to materialize/run through the harness — the 'patches' obligation is vacuously satisfied.

Refinement.md audit: legs A1/A2/A3 are R / I-of-R only (List[int]<->list-of-(name,estimator) tuples, one element per stage, cardinality-preserving; Nagini len <-> Python builtin len). Section B correctly records no consumed axiom and no A-reference; Section C correctly records no kind-3 step; the one genuinely-changed op (introduce a size query = collection cardinality) is modelled DEEPLY via len(steps) over the carrier, grounded in the actual input, not an opaque callee. Model<->patch correspondence holds: composite_size(steps) <-> Pipeline.__len__(self)=return len(self.steps) (gold hunk inserted between _iter and __getitem__). Because Result()==len(steps) is the tightest possible characterization and mutation is blocked, every verifying impl equals gold behaviour on all inputs; no verify=>correct gap is exhibitable. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-13439.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A composite estimator is built as an ORDERED collection of constituent
  stages. Client code that indexes the composite with an integer- or
  slice-based handle relies on the collection reporting its SIZE: a query for
  "how many stages does this composite hold?" must return the exact number of
  stages it was constructed from — every stage counted once, including the
  final stage and any inert placeholder stages, none omitted and none counted
  twice. The size is therefore the cardinality of the stage collection itself,
  so that an index handle spanning "from the start up to the size" covers the
  whole collection.

The stage collection is modelled as `List[int]`, one element per stage (the
element values — the (name, estimator) pairs — are irrelevant; only the
cardinality is observed). The reported size is an `int` equal to the length of
that collection. No callee is axiomatized: the behaviour is the length of the
input collection, modelled deeply.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No axiomatized callees: the reported size is the length of the input
#  collection, modelled deeply.)
# axioms-end


# pure-start
# (No pure helpers needed.)
# pure-end


def composite_size(steps: List[int]) -> int:
    # pre-conditions-start
    # The stage collection is read-only: the size query never mutates it, so it
    # is required AND ensured at fractional permission (directive 5).
    Requires(Acc(list_pred(steps), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(steps), 1 / 2))
    # The reported size is exactly the cardinality of the stage collection:
    # every stage counted once (final stage and inert placeholders included),
    # none omitted. Grounded in the actual input collection.
    Ensures(Result() == len(steps))
    # post-conditions-end
    # impl-start
    return len(steps)
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec: composite_size(steps: List[int]) -> int with Requires/Ensures Acc(list_pred(steps),1/2) (read-only, required AND ensured) and Ensures(Result() == len(steps)). This postcondition pins the return value EXACTLY for every input, and the fractional-permission-preserved-not-full contract blocks any impl from satisfying the spec by mutating steps. axioms region is genuinely empty (comment-only) — no @ContractOnly callee, no @Pure helper, no A-consumed/A-reference leg, no deep model standing in for a real callee, so G-AX is vacuous and there is nothing to falsify on the A-legs.

Battery (all copied from model.py, ONLY impl region edited; axioms/@Pure/Requires/Ensures byte-identical; same-spec spot-checked SAME on atk_1 and atk_6):
  atk_1 = return len(steps)-1  (PREPATCH bug: terminal-stage-dropping under-count, mirrors _iter(with_final=False))
  atk_2 = return len(steps)+1  (off-by-one high)
  atk_3 = return 0            (constant/ungrounded)
  atk_4 = 1 on empty else len (partial-domain, boundary N==0)
  atk_5 = return len(steps)*2 (scaling/double-count)
  atk_6 = steps.append(0); return len(steps) (control-flow-effect: mutation of read-only list)
  atk_7 = return 2            (ungrounded-oracle echo of the F2P 2-step answer)

Command per attack: python -m swebench_unified.adversary weakness nagini scikit-learn__scikit-learn-13439 atk_N.py (run concurrently in 3 batches, ≤3 JVMs).
Results: ALL SEVEN returned exit 2 = NOT-A-COUNTEREXAMPLE ('attack does not verify (verification failed) — the spec rejected this impl'). atk_6 fails precisely because the read-only 1/2 permission (Ensures Acc(...,1/2)) forbids append. Positive control (verbatim model impl 'return len(steps)') verifies: bash scripts/nagini_verify.sh pos_control.py -> exit 0, 'Verification successful' (12.0s).

Since NO attack is a CANDIDATE (none shares-spec-AND-verifies), there is no verifying wrong impl and thus no faithful refined patch to materialize/run through the harness — the 'patches' obligation is vacuously satisfied.

Refinement.md audit: legs A1/A2/A3 are R / I-of-R only (List[int]<->list-of-(name,estimator) tuples, one element per stage, cardinality-preserving; Nagini len <-> Python builtin len). Section B correctly records no consumed axiom and no A-reference; Section C correctly records no kind-3 step; the one genuinely-changed op (introduce a size query = collection cardinality) is modelled DEEPLY via len(steps) over the carrier, grounded in the actual input, not an opaque callee. Model<->patch correspondence holds: composite_size(steps) <-> Pipeline.__len__(self)=return len(self.steps) (gold hunk inserted between _iter and __getitem__). Because Result()==len(steps) is the tightest possible characterization and mutation is blocked, every verifying impl equals gold behaviour on all inputs; no verify=>correct gap is exhibitable. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The modeled function composite_size(steps: List[int]) -> int with postcondition Result() == len(steps) faithfully models the real callee Pipeline.__len__ (sklearn/pipeline.py: 'return len(self.steps)', confirmed verbatim in the base-commit worktree). Under the mapping.md/refinement.md R-refinement (self.steps -> List[int], one opaque element per stage, len<->len), for any N-stage pipeline the real len(pipe) returns N and the model returns len(steps)=N. They agree on the entire input domain (all finite stage counts N>=0). No axioms are consumed (axioms region empty), so the spec is fully grounded in the input collection's cardinality — the postcondition is exactly len(self.steps), neither too strong nor drifting. The read-only fractional permission Acc(list_pred(steps),1/2) required AND ensured correctly forbids mutation, matching that __len__ mutates nothing. G-CONF independently corroborates: shadow (contract-stripped impl) vs real len(pipe) agree on 100,015 composites (boundary N=0,1,2,3,50 + F2P 2-step + 1e5 fuzz over transformer/None/'passthrough' stage kinds, seed 13439), zero disagreements. No diverging input exists; the spec faithfully captures real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage surface = solver-facing spec view = model.py module docstring + Requires/Ensures for composite_size (mapping.md and refinement.md are audit/twin-artifact docs, excluded). Gold edit (public patch): adds `def __len__(self): return len(self.steps)` to sklearn/pipeline.py between _iter and __getitem__.

Public problem_statement already discloses everything the spec conveys: it is titled 'Pipeline should implement __len__', states that `pipe[:len(pipe)]` raises because __len__ is missing, and reproduces with a 2-step Pipeline. It explicitly requests implementing __len__ on the Pipeline.

Spec view content: docstring frames the behaviour abstractly ('composite estimator built as an ORDERED collection of stages'; 'a query for how many stages must return the exact number of stages'), and the discriminating postcondition is `Result() == len(steps)`. This 'reported size = full cardinality of the stage collection' is exactly the obvious/only-sensible semantics of implementing __len__ on an ordered collection — directly implied by the public issue, adding nothing beyond it.

The spec view names NO repo symbol (Pipeline, __len__, self.steps), NO file path (sklearn/pipeline.py), NO edit location (insertion between _iter/__getitem__), and NO base_commit. All those concrete gold-edit details live only in mapping.md / refinement.md, which are outside the leakage surface. The mechanical G-LEAK screen also passed ('spec view clean', failures=[]). No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
