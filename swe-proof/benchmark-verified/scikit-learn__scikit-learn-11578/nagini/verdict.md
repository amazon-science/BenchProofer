# P2 adversarial audit — scikit-learn__scikit-learn-11578

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_identity.py`, `atk2_swap.py`, `atk3_partial_ovr_wrong.py`, `atk4_always_softmax.py`, `atk5_always_ovr.py`, `atk6_mode_negate.py`, `atk_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk7_echo_inline.py`, `atk8_defensive_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_identity.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -100,7 +99,6 @@
     # The two probability transforms genuinely differ on the witness row (the
     # audited reference, G-AX).
     Requires(transforms_differ())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The scoring estimator runs in the SAME mode the helper was asked for, so
@@ -118,9 +116,6 @@
                     Result() != proba_ovr(d)))
     # post-conditions-end
     # impl-start
-    # The scoring estimator inherits the caller's multiclass mode, so its
-    # probability output is that mode's transform of the decision row.
-    effective_mode = caller_mode  # type: int
-    result = scoring_proba(effective_mode, d)  # type: PSeq[int]
+    result = d  # type: PSeq[int]
     return result
     # impl-end
```

Attack 2 — `atk2_swap.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -100,7 +99,6 @@
     # The two probability transforms genuinely differ on the witness row (the
     # audited reference, G-AX).
     Requires(transforms_differ())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The scoring estimator runs in the SAME mode the helper was asked for, so
@@ -118,9 +116,9 @@
                     Result() != proba_ovr(d)))
     # post-conditions-end
     # impl-start
-    # The scoring estimator inherits the caller's multiclass mode, so its
-    # probability output is that mode's transform of the decision row.
-    effective_mode = caller_mode  # type: int
-    result = scoring_proba(effective_mode, d)  # type: PSeq[int]
+    if caller_mode == MULTINOMIAL:
+        result = proba_ovr(d)  # type: PSeq[int]
+    else:
+        result = proba_softmax(d)
     return result
     # impl-end
```

Attack 3 — `atk3_partial_ovr_wrong.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -100,7 +99,6 @@
     # The two probability transforms genuinely differ on the witness row (the
     # audited reference, G-AX).
     Requires(transforms_differ())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The scoring estimator runs in the SAME mode the helper was asked for, so
@@ -118,9 +116,9 @@
                     Result() != proba_ovr(d)))
     # post-conditions-end
     # impl-start
-    # The scoring estimator inherits the caller's multiclass mode, so its
-    # probability output is that mode's transform of the decision row.
-    effective_mode = caller_mode  # type: int
-    result = scoring_proba(effective_mode, d)  # type: PSeq[int]
+    if caller_mode == MULTINOMIAL:
+        result = proba_softmax(d)  # type: PSeq[int]
+    else:
+        result = proba_softmax(d)
     return result
     # impl-end
```

Attack 4 — `atk4_always_softmax.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -100,7 +99,6 @@
     # The two probability transforms genuinely differ on the witness row (the
     # audited reference, G-AX).
     Requires(transforms_differ())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The scoring estimator runs in the SAME mode the helper was asked for, so
@@ -118,9 +116,6 @@
                     Result() != proba_ovr(d)))
     # post-conditions-end
     # impl-start
-    # The scoring estimator inherits the caller's multiclass mode, so its
-    # probability output is that mode's transform of the decision row.
-    effective_mode = caller_mode  # type: int
-    result = scoring_proba(effective_mode, d)  # type: PSeq[int]
+    result = proba_softmax(d)  # type: PSeq[int]
     return result
     # impl-end
```

Attack 5 — `atk5_always_ovr.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -100,7 +99,6 @@
     # The two probability transforms genuinely differ on the witness row (the
     # audited reference, G-AX).
     Requires(transforms_differ())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The scoring estimator runs in the SAME mode the helper was asked for, so
@@ -118,9 +116,6 @@
                     Result() != proba_ovr(d)))
     # post-conditions-end
     # impl-start
-    # The scoring estimator inherits the caller's multiclass mode, so its
-    # probability output is that mode's transform of the decision row.
-    effective_mode = caller_mode  # type: int
-    result = scoring_proba(effective_mode, d)  # type: PSeq[int]
+    result = proba_ovr(d)  # type: PSeq[int]
     return result
     # impl-end
```

Attack 6 — `atk6_mode_negate.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -100,7 +99,6 @@
     # The two probability transforms genuinely differ on the witness row (the
     # audited reference, G-AX).
     Requires(transforms_differ())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The scoring estimator runs in the SAME mode the helper was asked for, so
@@ -118,9 +116,7 @@
                     Result() != proba_ovr(d)))
     # post-conditions-end
     # impl-start
-    # The scoring estimator inherits the caller's multiclass mode, so its
-    # probability output is that mode's transform of the decision row.
-    effective_mode = caller_mode  # type: int
+    effective_mode = 1 - caller_mode  # type: int
     result = scoring_proba(effective_mode, d)  # type: PSeq[int]
     return result
     # impl-end
```

Attack 7 — `atk7_echo_inline.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -100,7 +99,6 @@
     # The two probability transforms genuinely differ on the witness row (the
     # audited reference, G-AX).
     Requires(transforms_differ())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The scoring estimator runs in the SAME mode the helper was asked for, so
@@ -118,9 +116,9 @@
                     Result() != proba_ovr(d)))
     # post-conditions-end
     # impl-start
-    # The scoring estimator inherits the caller's multiclass mode, so its
-    # probability output is that mode's transform of the decision row.
-    effective_mode = caller_mode  # type: int
-    result = scoring_proba(effective_mode, d)  # type: PSeq[int]
+    if caller_mode == MULTINOMIAL:
+        result = proba_softmax(d)  # type: PSeq[int]
+    else:
+        result = proba_ovr(d)
     return result
     # impl-end
```

Attack 8 — `atk8_defensive_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -100,7 +99,6 @@
     # The two probability transforms genuinely differ on the witness row (the
     # audited reference, G-AX).
     Requires(transforms_differ())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The scoring estimator runs in the SAME mode the helper was asked for, so
@@ -118,9 +116,9 @@
                     Result() != proba_ovr(d)))
     # post-conditions-end
     # impl-start
-    # The scoring estimator inherits the caller's multiclass mode, so its
-    # probability output is that mode's transform of the decision row.
     effective_mode = caller_mode  # type: int
+    if effective_mode != OVR and effective_mode != MULTINOMIAL:
+        effective_mode = OVR
     result = scoring_proba(effective_mode, d)  # type: PSeq[int]
     return result
     # impl-end
```

Attack 9 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

```diff
@@ -34,7 +34,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -100,7 +99,6 @@
     # The two probability transforms genuinely differ on the witness row (the
     # audited reference, G-AX).
     Requires(transforms_differ())
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The scoring estimator runs in the SAME mode the helper was asked for, so
@@ -118,9 +116,11 @@
                     Result() != proba_ovr(d)))
     # post-conditions-end
     # impl-start
-    # The scoring estimator inherits the caller's multiclass mode, so its
-    # probability output is that mode's transform of the decision row.
-    effective_mode = caller_mode  # type: int
+    # Pre-patch skeleton: the throw-away scoring estimator is built WITHOUT
+    # passing the caller's multiclass mode, so it always falls back to the
+    # default one-vs-rest mode regardless of the caller's request. Its
+    # probability output is therefore always the one-vs-rest transform.
+    effective_mode = OVR  # type: int
     result = scoring_proba(effective_mode, d)  # type: PSeq[int]
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-11578.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A cross-validation helper computes a score for fitted multiclass logistic
  coefficients by handing them to a throw-away scoring estimator and asking a
  scorer for a number. The classifier supports two multiclass modes, selected
  by a flag ``multi_class``:

    * the one-vs-rest mode normalises a per-class logistic response, and
    * the multinomial mode applies a softmax to the per-class decision scores.

  The two modes induce DIFFERENT class-probability vectors from the same
  per-class decision scores (they agree only degenerately).

  The behaviour that matters: the scoring estimator the helper builds must use
  the SAME ``multi_class`` mode that the helper itself was asked to operate in.
  Consequently a probability-consuming scorer (one that reads the predicted
  class-probability vector) sees the multinomial probabilities when the helper
  runs in multinomial mode — NOT the one-vs-rest probabilities.

Modelling choices (Nagini fragment):
  * The multiclass mode is an ``int`` tag: ``OVR`` (0) and ``MULTINOMIAL`` (1).
  * The per-class decision scores of one test sample are a ``PSeq[int]`` (the
    real per-class real-valued decision row, refined to integer code points;
    only the SELECTION between the two probability transforms is the behaviour
    under specification, so the transforms are opaque references validated
    against their real numeric callees out-of-band by axiom_check.py / G-AX).
  * The two probability transforms ``proba_softmax`` and ``proba_ovr`` are
    distinct total functions of the decision row that DIFFER on a witness row.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def proba_softmax(d: PSeq[int]) -> PSeq[int]:
    """The multinomial class-probability vector induced by the per-class
    decision row ``d`` (the softmax transform). Opaque reference: its real
    numeric callee and its distinctness from the one-vs-rest transform are
    validated by axiom_check.py (G-AX). See mapping.md."""
    Ensures(len(Result()) == len(d))


@Pure
@ContractOnly
def proba_ovr(d: PSeq[int]) -> PSeq[int]:
    """The one-vs-rest class-probability vector induced by the per-class
    decision row ``d`` (normalised per-class logistic response). Opaque
    reference validated by axiom_check.py (G-AX). See mapping.md."""
    Ensures(len(Result()) == len(d))


@Pure
@ContractOnly
def witness_decision() -> PSeq[int]:
    """A per-class decision row on which the two probability transforms
    genuinely differ — the situation a multiclass test exercises. Existence is
    witnessed by axiom_check.py running the real transforms (G-AX)."""
    Ensures(len(Result()) >= 2)


@Pure
@ContractOnly
def transforms_differ() -> bool:
    """The two probability transforms are NOT the same function: on the witness
    decision row they yield different probability vectors. Validated against the
    real softmax / one-vs-rest callees by axiom_check.py (G-AX)."""
    Ensures(Implies(Result(), proba_softmax(witness_decision())
                    != proba_ovr(witness_decision())))
# axioms-end


# pure-start
OVR = 0          # the one-vs-rest multiclass mode tag
MULTINOMIAL = 1  # the multinomial (softmax) multiclass mode tag


@Pure
def scoring_proba(mode: int, d: PSeq[int]) -> PSeq[int]:
    """The class-probability vector the scoring estimator produces for a test
    sample with per-class decision row ``d`` when operating in ``mode``: the
    softmax (multinomial) transform in multinomial mode, otherwise the
    one-vs-rest transform."""
    if mode == MULTINOMIAL:
        return proba_softmax(d)
    return proba_ovr(d)
# pure-end


def scoring_estimator_proba(caller_mode: int, d: PSeq[int]) -> PSeq[int]:
    # pre-conditions-start
    Requires(caller_mode == OVR or caller_mode == MULTINOMIAL)
    # The two probability transforms genuinely differ on the witness row (the
    # audited reference, G-AX).
    Requires(transforms_differ())
    # pre-conditions-end
    # post-conditions-start
    # The scoring estimator runs in the SAME mode the helper was asked for, so
    # the probability vector it produces is that mode's transform of ``d``.
    Ensures(Result() == scoring_proba(caller_mode, d))
    # The discriminating consequence: in multinomial mode the probability
    # vector is the multinomial (softmax) one ...
    Ensures(Implies(caller_mode == MULTINOMIAL, Result() == proba_softmax(d)))
    # ... and in one-vs-rest mode it is the one-vs-rest one.
    Ensures(Implies(caller_mode == OVR, Result() == proba_ovr(d)))
    # Therefore, on a decision row where the two transforms differ, a
    # multinomial-mode score is NOT the one-vs-rest probability vector that the
    # default (mode-ignoring) estimator would have produced.
    Ensures(Implies(caller_mode == MULTINOMIAL and d == witness_decision(),
                    Result() != proba_ovr(d)))
    # post-conditions-end
    # impl-start
    # The scoring estimator inherits the caller's multiclass mode, so its
    # probability output is that mode's transform of the decision row.
    effective_mode = caller_mode  # type: int
    result = scoring_proba(effective_mode, d)  # type: PSeq[int]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for scikit-learn__scikit-learn-11578 (nagini). env python (adversary CLI), scripts/nagini_verify.sh for direct verify. Impl region is the only edited region in every attack; axioms/@Pure/Requires/Ensures left byte-identical (same-spec confirmed exit 0 on samples: atk1,atk2,atk7,atk8).

POSITIVE CONTROL: positive_control.py (= model.py verbatim) -> nagini_verify.sh 'Verification successful' (12.16s). PASS.
PREPATCH: atk_prepatch.py (= model_prepatch.py, effective_mode=OVR) -> weakness exit=2 'attack does not verify' — spec REJECTS the prepatch bug (G-DIFF holds, post-condition #1 Result()==scoring_proba(caller_mode,d) fails on MULTINOMIAL). prepatch_reproduced=true.

atk1_identity (return d; ungrounded) exit=2 REJECTED (does not verify).
- atk2_swap (branches swapped: softmax on OVR, ovr on MULTINOMIAL; control-flow-effect) exit=2 REJECTED.
- atk3_partial_ovr_wrong (softmax on both modes; partial-domain, OVR case wrong) exit=2 REJECTED.
- atk4_always_softmax (boundary: hardcode softmax; fails OVR post #3) exit=2 REJECTED.
- atk5_always_ovr (hardcode ovr; prepatch behavior, distinct encoding) exit=2 REJECTED.
- atk6_mode_negate (effective_mode=1-caller_mode; flips modes) exit=2 REJECTED.
- atk7_echo_inline (if caller_mode==MULTINOMIAL: proba_softmax(d) else proba_ovr(d) — inline spelling of scoring_proba) exit=0 CANDIDATE (shares spec AND verifies, 14.0s).
- atk8_defensive_echo (effective_mode=caller_mode + dead defensive branch normalizing out-of-domain modes to OVR; branch dead under Requires) exit=0 CANDIDATE (14.8s).

Every CANDIDATE's faithful refined patch materialized and RUN through the official harness (swebench_unified.harness.run_resolve, docker, timeout 1800). Both atk7 and atk8 refine, under refinement.md's map (A2 R+I: effective_mode=caller_mode <-> LogisticRegression(multi_class=multi_class); A3 A-reference: scoring_proba selector <-> predict_proba mode dispatch), to the identical real-code operation — the scoring estimator inheriting the caller's multi_class — i.e. the GOLD patch verbatim (atk8's extra branch is dead because the precondition restricts caller_mode to {OVR,MULTINOMIAL}; real sklearn raises ValueError otherwise, so it introduces no observable behavior). Faithful patch = faithful_patch.diff (= benchmark patch.diff): RESOLVED=True, COMPLETED=True, NOTE='resolved'. Both candidates are behaviorally-faithful echoes of the gold; per the sanctioned 'a resolving echo is NOT a weakness' policy (candidate->resolve check), they do NOT break the spec.

A-LEG AUDIT (refinement.md/mapping.md): legs are A1=R, A2=R+I, A3=A-reference (proba_softmax/proba_ovr validated == real predict_proba softmax/_predict_proba_lr branches by axiom_check.py/G-AX over 2000 randomized multiclass instances), A4=I, plus exactly ONE A-consumed axiom transforms_differ (existential distinctness on a witness row, discharges derived post-condition #4 only, NOT load-bearing for the differential which post #1 carries). Section B explicitly certifies NO kind-3 leg; the one genuinely-changed op (estimator inherits caller mode vs default OVR) is modeled DEEPLY via scoring_proba, not hidden behind an axiom. A-reference correspondence to the real callees holds (axiom_check.py imports real numpy+sklearn, the unchanged softmax/_predict_proba_lr/predict_proba dispatch). transforms_differ is an existential (not the unsound arg-max universal), so not an answer-key oracle the impl can echo. No over-claim / no kind-3.

VERDICT: SOUND. 8 attacks + prepatch run; 6 wrong impls correctly rejected; the 2 verifying impls are gold-equivalent echoes whose materialized faithful patch RESOLVES under the official harness. No verifying same-spec impl yields a non-resolving faithful patch, so verify => correct holds. Positive control verifies; prepatch reproduced.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_identity.py`, `atk2_swap.py`, `atk3_partial_ovr_wrong.py`, `atk4_always_softmax.py`, `atk5_always_ovr.py`, `atk6_mode_negate.py`, `atk_prepatch.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk7_echo_inline.py`, `atk8_defensive_echo.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_identity.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_swap.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_partial_ovr_wrong.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_always_softmax.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_always_ovr.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_mode_negate.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_echo_inline.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk8_defensive_echo.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_prepatch.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for scikit-learn__scikit-learn-11578.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A cross-validation helper computes a score for fitted multiclass logistic
  coefficients by handing them to a throw-away scoring estimator and asking a
  scorer for a number. The classifier supports two multiclass modes, selected
  by a flag ``multi_class``:

    * the one-vs-rest mode normalises a per-class logistic response, and
    * the multinomial mode applies a softmax to the per-class decision scores.

  The two modes induce DIFFERENT class-probability vectors from the same
  per-class decision scores (they agree only degenerately).

  The behaviour that matters: the scoring estimator the helper builds must use
  the SAME ``multi_class`` mode that the helper itself was asked to operate in.
  Consequently a probability-consuming scorer (one that reads the predicted
  class-probability vector) sees the multinomial probabilities when the helper
  runs in multinomial mode — NOT the one-vs-rest probabilities.

Modelling choices (Nagini fragment):
  * The multiclass mode is an ``int`` tag: ``OVR`` (0) and ``MULTINOMIAL`` (1).
  * The per-class decision scores of one test sample are a ``PSeq[int]`` (the
    real per-class real-valued decision row, refined to integer code points;
    only the SELECTION between the two probability transforms is the behaviour
    under specification, so the transforms are opaque references validated
    against their real numeric callees out-of-band by axiom_check.py / G-AX).
  * The two probability transforms ``proba_softmax`` and ``proba_ovr`` are
    distinct total functions of the decision row that DIFFER on a witness row.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def proba_softmax(d: PSeq[int]) -> PSeq[int]:
    """The multinomial class-probability vector induced by the per-class
    decision row ``d`` (the softmax transform). Opaque reference: its real
    numeric callee and its distinctness from the one-vs-rest transform are
    validated by axiom_check.py (G-AX). See mapping.md."""
    Ensures(len(Result()) == len(d))


@Pure
@ContractOnly
def proba_ovr(d: PSeq[int]) -> PSeq[int]:
    """The one-vs-rest class-probability vector induced by the per-class
    decision row ``d`` (normalised per-class logistic response). Opaque
    reference validated by axiom_check.py (G-AX). See mapping.md."""
    Ensures(len(Result()) == len(d))


@Pure
@ContractOnly
def witness_decision() -> PSeq[int]:
    """A per-class decision row on which the two probability transforms
    genuinely differ — the situation a multiclass test exercises. Existence is
    witnessed by axiom_check.py running the real transforms (G-AX)."""
    Ensures(len(Result()) >= 2)


@Pure
@ContractOnly
def transforms_differ() -> bool:
    """The two probability transforms are NOT the same function: on the witness
    decision row they yield different probability vectors. Validated against the
    real softmax / one-vs-rest callees by axiom_check.py (G-AX)."""
    Ensures(Implies(Result(), proba_softmax(witness_decision())
                    != proba_ovr(witness_decision())))
# axioms-end


# pure-start
OVR = 0          # the one-vs-rest multiclass mode tag
MULTINOMIAL = 1  # the multinomial (softmax) multiclass mode tag


@Pure
def scoring_proba(mode: int, d: PSeq[int]) -> PSeq[int]:
    """The class-probability vector the scoring estimator produces for a test
    sample with per-class decision row ``d`` when operating in ``mode``: the
    softmax (multinomial) transform in multinomial mode, otherwise the
    one-vs-rest transform."""
    if mode == MULTINOMIAL:
        return proba_softmax(d)
    return proba_ovr(d)
# pure-end


def scoring_estimator_proba(caller_mode: int, d: PSeq[int]) -> PSeq[int]:
    # pre-conditions-start
    Requires(caller_mode == OVR or caller_mode == MULTINOMIAL)
    # The two probability transforms genuinely differ on the witness row (the
    # audited reference, G-AX).
    Requires(transforms_differ())
    # pre-conditions-end
    # post-conditions-start
    # The scoring estimator runs in the SAME mode the helper was asked for, so
    # the probability vector it produces is that mode's transform of ``d``.
    Ensures(Result() == scoring_proba(caller_mode, d))
    # The discriminating consequence: in multinomial mode the probability
    # vector is the multinomial (softmax) one ...
    Ensures(Implies(caller_mode == MULTINOMIAL, Result() == proba_softmax(d)))
    # ... and in one-vs-rest mode it is the one-vs-rest one.
    Ensures(Implies(caller_mode == OVR, Result() == proba_ovr(d)))
    # Therefore, on a decision row where the two transforms differ, a
    # multinomial-mode score is NOT the one-vs-rest probability vector that the
    # default (mode-ignoring) estimator would have produced.
    Ensures(Implies(caller_mode == MULTINOMIAL and d == witness_decision(),
                    Result() != proba_ovr(d)))
    # post-conditions-end
    # impl-start
    # The scoring estimator inherits the caller's multiclass mode, so its
    # probability output is that mode's transform of the decision row.
    effective_mode = caller_mode  # type: int
    result = scoring_proba(effective_mode, d)  # type: PSeq[int]
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for scikit-learn__scikit-learn-11578 (nagini). env python (adversary CLI), scripts/nagini_verify.sh for direct verify. Impl region is the only edited region in every attack; axioms/@Pure/Requires/Ensures left byte-identical (same-spec confirmed exit 0 on samples: atk1,atk2,atk7,atk8).

POSITIVE CONTROL: positive_control.py (= model.py verbatim) -> nagini_verify.sh 'Verification successful' (12.16s). PASS.
PREPATCH: atk_prepatch.py (= model_prepatch.py, effective_mode=OVR) -> weakness exit=2 'attack does not verify' — spec REJECTS the prepatch bug (G-DIFF holds, post-condition #1 Result()==scoring_proba(caller_mode,d) fails on MULTINOMIAL). prepatch_reproduced=true.

atk1_identity (return d; ungrounded) exit=2 REJECTED (does not verify).
- atk2_swap (branches swapped: softmax on OVR, ovr on MULTINOMIAL; control-flow-effect) exit=2 REJECTED.
- atk3_partial_ovr_wrong (softmax on both modes; partial-domain, OVR case wrong) exit=2 REJECTED.
- atk4_always_softmax (boundary: hardcode softmax; fails OVR post #3) exit=2 REJECTED.
- atk5_always_ovr (hardcode ovr; prepatch behavior, distinct encoding) exit=2 REJECTED.
- atk6_mode_negate (effective_mode=1-caller_mode; flips modes) exit=2 REJECTED.
- atk7_echo_inline (if caller_mode==MULTINOMIAL: proba_softmax(d) else proba_ovr(d) — inline spelling of scoring_proba) exit=0 CANDIDATE (shares spec AND verifies, 14.0s).
- atk8_defensive_echo (effective_mode=caller_mode + dead defensive branch normalizing out-of-domain modes to OVR; branch dead under Requires) exit=0 CANDIDATE (14.8s).

Every CANDIDATE's faithful refined patch materialized and RUN through the official harness (swebench_unified.harness.run_resolve, docker, timeout 1800). Both atk7 and atk8 refine, under refinement.md's map (A2 R+I: effective_mode=caller_mode <-> LogisticRegression(multi_class=multi_class); A3 A-reference: scoring_proba selector <-> predict_proba mode dispatch), to the identical real-code operation — the scoring estimator inheriting the caller's multi_class — i.e. the GOLD patch verbatim (atk8's extra branch is dead because the precondition restricts caller_mode to {OVR,MULTINOMIAL}; real sklearn raises ValueError otherwise, so it introduces no observable behavior). Faithful patch = faithful_patch.diff (= benchmark patch.diff): RESOLVED=True, COMPLETED=True, NOTE='resolved'. Both candidates are behaviorally-faithful echoes of the gold; per the sanctioned 'a resolving echo is NOT a weakness' policy (candidate->resolve check), they do NOT break the spec.

A-LEG AUDIT (refinement.md/mapping.md): legs are A1=R, A2=R+I, A3=A-reference (proba_softmax/proba_ovr validated == real predict_proba softmax/_predict_proba_lr branches by axiom_check.py/G-AX over 2000 randomized multiclass instances), A4=I, plus exactly ONE A-consumed axiom transforms_differ (existential distinctness on a witness row, discharges derived post-condition #4 only, NOT load-bearing for the differential which post #1 carries). Section B explicitly certifies NO kind-3 leg; the one genuinely-changed op (estimator inherits caller mode vs default OVR) is modeled DEEPLY via scoring_proba, not hidden behind an axiom. A-reference correspondence to the real callees holds (axiom_check.py imports real numpy+sklearn, the unchanged softmax/_predict_proba_lr/predict_proba dispatch). transforms_differ is an existential (not the unsound arg-max universal), so not an answer-key oracle the impl can echo. No over-claim / no kind-3.

VERDICT: SOUND. 8 attacks + prepatch run; 6 wrong impls correctly rejected; the 2 verifying impls are gold-equivalent echoes whose materialized faithful patch RESOLVES under the official harness. No verifying same-spec impl yields a non-resolving faithful patch, so verify => correct holds. Positive control verifies; prepatch reproduced.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong/drift) check for scikit-learn__scikit-learn-11578 nagini. The modeled function scoring_estimator_proba(caller_mode, d) abstracts the gold change LogisticRegression(multi_class=multi_class) at _log_reg_scoring_path (logistic.py:925). No diverging input found; the spec does NOT over-claim relative to the real repo callees.

Evidence:
1. model.py verifies (Nagini, 12.1s); model_prepatch.py (effective_mode=OVR) FAILS on postcondition #1 (Result()==scoring_proba(caller_mode,d)) — the differential is real and grounded in modeled inputs, not the axiom.
2. Spec regions (axioms..post-conditions) are byte-identical between model.py and model_prepatch.py; only the impl region differs. `same-spec` toolkit returns SAME (exit 0).
3. G-AX (axiom_check.py) passes against real scikit-learn 1.3.0: over 2000 random fitted LogisticRegression pairs, decision_function is mode-independent, predict_proba routes softmax<->multinomial and normalized-OvR<->ovr, a witness row where the two transforms differ exists, and neg-log-loss discriminates the modes. The real predict_proba dispatch (logistic.py:1343-1353) and LinearClassifierMixin._predict_proba_lr (base.py: expit then row-normalize for multiclass) exactly match the modeled proba_softmax/proba_ovr references.
4. The spec is deliberately CONSERVATIVE: transforms_differ is an existential (not universal) fact; the refinement/mapping explicitly refuse to assert arg-max (predicted-class) agreement between the transforms, because that is false once a decision coordinate saturates the sigmoid (~36.74). Encoding it would have been the plausible over-claim, and it is intentionally absent from both the contract and axiom_check.py. Every postcondition (result-pinning #1, mode-specific #2/#3, witness-inequality #4) is validated true against the real callees.

No input on which the modeled function disagrees with the real callee was found. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: LogisticRegression(fit_intercept=fit_intercept) -> LogisticRegression(multi_class=multi_class) in _log_reg_scoring_path (logistic.py:922/925). The public problem_statement ALREADY discloses the fix in full: it quotes the buggy line verbatim, states it defaults multi_class='ovr', explains ovr=normalised one-vs-rest logistic response vs multinomial=softmax, that they differ, that neg_log_loss reads predict_proba, and literally proposes the fix `LogisticRegression(fit_intercept=fit_intercept, multi_class=multi_class)` so the estimator inherits the multi_class option.

Spec view checked line by line against problem_statement (NOT hints_text):
(a) docstring 'ovr normalises a per-class logistic response / multinomial applies softmax' + 'the two modes induce DIFFERENT class-probability vectors' -> already in problem_statement (ovr_approach vs softmax, differing probs).
(b) 'the scoring estimator must use the SAME multi_class mode the helper was asked for' + 'probability-consuming scorer sees multinomial probabilities NOT one-vs-rest' -> paraphrase of the problem_statement's own proposed fix and observed symptom.
(c) Nagini-fragment modeling (int tags OVR/MULTINOMIAL, PSeq[int], opaque proba_softmax/proba_ovr/witness_decision/transforms_differ) is pure abstraction disclosing nothing about the concrete edit; postconditions (Result()==scoring_proba(caller_mode,d); softmax in MULTINOMIAL, ovr in OVR) restate already-public desired inheritance behavior.

Notably the spec view discloses STRICTLY LESS about the concrete edit than problem_statement: it never mentions fit_intercept being dropped nor names the constructor site (logistic.py:925). Impl region correctly elided (verified via swebench_unified.markers.spec_view with nagini backend: impl-start shows '... implementation elided'). Every modeled fact is derivable from the already-public behavioral description. No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
