# P2 adversarial audit — matplotlib__matplotlib-25287

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -59,7 +58,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base_color), 1 / 2))
     Requires(Acc(list_pred(label_color), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base_color), 1 / 2))
@@ -74,10 +72,7 @@
                     ToSeq(Result()) == ToSeq(label_color)))
     # post-conditions-end
     # impl-start
-    if ToSeq(label_color) == sentinel_inherit():
-        tick_color = list(base_color)  # type: List[int]
-    else:
-        tick_color = list(label_color)
+    tick_color = list(base_color)  # type: List[int]
     return tick_color
     # impl-end
 
@@ -86,7 +81,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base_color), 1 / 2))
     Requires(Acc(list_pred(label_color), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base_color), 1 / 2))
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -59,7 +58,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base_color), 1 / 2))
     Requires(Acc(list_pred(label_color), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base_color), 1 / 2))
@@ -74,10 +72,7 @@
                     ToSeq(Result()) == ToSeq(label_color)))
     # post-conditions-end
     # impl-start
-    if ToSeq(label_color) == sentinel_inherit():
-        tick_color = list(base_color)  # type: List[int]
-    else:
-        tick_color = list(label_color)
+    tick_color = list(label_color)  # type: List[int]
     return tick_color
     # impl-end
 
@@ -86,7 +81,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base_color), 1 / 2))
     Requires(Acc(list_pred(label_color), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base_color), 1 / 2))
@@ -99,9 +93,6 @@
                     ToSeq(Result()) == ToSeq(label_color)))
     # post-conditions-end
     # impl-start
-    if ToSeq(label_color) == sentinel_inherit():
-        tick_color = list(base_color)  # type: List[int]
-    else:
-        tick_color = list(label_color)
+    tick_color = list(label_color)  # type: List[int]
     return tick_color
     # impl-end
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -59,7 +58,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base_color), 1 / 2))
     Requires(Acc(list_pred(label_color), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base_color), 1 / 2))
@@ -74,7 +72,7 @@
                     ToSeq(Result()) == ToSeq(label_color)))
     # post-conditions-end
     # impl-start
-    if ToSeq(label_color) == sentinel_inherit():
+    if ToSeq(label_color) == PSeq(105, 110, 104, 101, 114, 105):
         tick_color = list(base_color)  # type: List[int]
     else:
         tick_color = list(label_color)
@@ -86,7 +84,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base_color), 1 / 2))
     Requires(Acc(list_pred(label_color), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base_color), 1 / 2))
@@ -99,7 +96,7 @@
                     ToSeq(Result()) == ToSeq(label_color)))
     # post-conditions-end
     # impl-start
-    if ToSeq(label_color) == sentinel_inherit():
+    if ToSeq(label_color) == PSeq(105, 110, 104, 101, 114, 105):
         tick_color = list(base_color)  # type: List[int]
     else:
         tick_color = list(label_color)
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -59,7 +58,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base_color), 1 / 2))
     Requires(Acc(list_pred(label_color), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base_color), 1 / 2))
@@ -74,10 +72,7 @@
                     ToSeq(Result()) == ToSeq(label_color)))
     # post-conditions-end
     # impl-start
-    if ToSeq(label_color) == sentinel_inherit():
-        tick_color = list(base_color)  # type: List[int]
-    else:
-        tick_color = list(label_color)
+    tick_color = []  # type: List[int]
     return tick_color
     # impl-end
 
@@ -86,7 +81,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base_color), 1 / 2))
     Requires(Acc(list_pred(label_color), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base_color), 1 / 2))
@@ -99,9 +93,6 @@
                     ToSeq(Result()) == ToSeq(label_color)))
     # post-conditions-end
     # impl-start
-    if ToSeq(label_color) == sentinel_inherit():
-        tick_color = list(base_color)  # type: List[int]
-    else:
-        tick_color = list(label_color)
+    tick_color = []  # type: List[int]
     return tick_color
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -59,7 +58,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base_color), 1 / 2))
     Requires(Acc(list_pred(label_color), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base_color), 1 / 2))
@@ -75,9 +73,9 @@
     # post-conditions-end
     # impl-start
     if ToSeq(label_color) == sentinel_inherit():
-        tick_color = list(base_color)  # type: List[int]
+        tick_color = list(label_color)  # type: List[int]
     else:
-        tick_color = list(label_color)
+        tick_color = list(base_color)
     return tick_color
     # impl-end
 
@@ -86,7 +84,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base_color), 1 / 2))
     Requires(Acc(list_pred(label_color), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base_color), 1 / 2))
@@ -100,8 +97,8 @@
     # post-conditions-end
     # impl-start
     if ToSeq(label_color) == sentinel_inherit():
-        tick_color = list(base_color)  # type: List[int]
+        tick_color = list(label_color)  # type: List[int]
     else:
-        tick_color = list(label_color)
+        tick_color = list(base_color)
     return tick_color
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -59,7 +58,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base_color), 1 / 2))
     Requires(Acc(list_pred(label_color), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base_color), 1 / 2))
@@ -86,7 +84,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base_color), 1 / 2))
     Requires(Acc(list_pred(label_color), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base_color), 1 / 2))
@@ -99,9 +96,6 @@
                     ToSeq(Result()) == ToSeq(label_color)))
     # post-conditions-end
     # impl-start
-    if ToSeq(label_color) == sentinel_inherit():
-        tick_color = list(base_color)  # type: List[int]
-    else:
-        tick_color = list(label_color)
+    tick_color = list(base_color)  # type: List[int]
     return tick_color
     # impl-end
```

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -29,7 +29,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -59,7 +58,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base_color), 1 / 2))
     Requires(Acc(list_pred(label_color), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base_color), 1 / 2))
@@ -75,9 +73,10 @@
     # post-conditions-end
     # impl-start
     if ToSeq(label_color) == sentinel_inherit():
-        tick_color = list(base_color)  # type: List[int]
+        chosen = base_color  # type: List[int]
     else:
-        tick_color = list(label_color)
+        chosen = label_color
+    tick_color = list(chosen)  # type: List[int]
     return tick_color
     # impl-end
 
@@ -86,7 +85,6 @@
     # pre-conditions-start
     Requires(Acc(list_pred(base_color), 1 / 2))
     Requires(Acc(list_pred(label_color), 1 / 2))
-    Requires(MustTerminate(6))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(base_color), 1 / 2))
@@ -100,8 +98,9 @@
     # post-conditions-end
     # impl-start
     if ToSeq(label_color) == sentinel_inherit():
-        tick_color = list(base_color)  # type: List[int]
+        chosen = base_color  # type: List[int]
     else:
-        tick_color = list(label_color)
+        chosen = label_color
+    tick_color = list(chosen)  # type: List[int]
     return tick_color
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-25287.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a secondary annotation that accompanies an axis derives its foreground
  colour from configuration, the colour it should take is the explicitly
  configured label colour. The configured label colour may carry a distinguished
  sentinel value meaning "do not override; defer to the base colour"; in that
  one case, and only that case, the base colour is used instead.

  Formally, for two configured colour values `base_color` and `label_color`
  (each a sequence of code points naming a colour), the effective colour of the
  derived annotation is:

      effective(base_color, label_color)
        = base_color              if label_color is the sentinel `inherit`
        = label_color             otherwise

This rule is applied at two independent configuration sites that differ only in
which pair of base/label colour values they read; both are modelled, each as its
own contracted function, because each is independently observable.

Colour names are modelled as `List[int]` of code points (Nagini bans `str`
indexing); the sentinel `inherit` is the constant code-point sequence for that
word. The result is a fresh sequence whose contents equal the chosen input's
contents. There are no axiomatized callees: the selection is expressed directly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def sentinel_inherit() -> PSeq[int]:
    # the code points of the word that means "defer to the base colour"
    # i n h e r i t
    return PSeq(105, 110, 104, 101, 114, 105, 116)


@Pure
def effective_color(base_color: PSeq[int], label_color: PSeq[int]) -> PSeq[int]:
    """The colour the derived annotation should take: the explicit label colour,
    except when the label colour is the sentinel, in which case the base
    colour."""
    if label_color == sentinel_inherit():
        return base_color
    return label_color
# pure-end


def offset_color_primary(base_color: List[int], label_color: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base_color), 1 / 2))
    Requires(Acc(list_pred(label_color), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base_color), 1 / 2))
    Ensures(Acc(list_pred(label_color), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The chosen colour is the label colour unless that is the sentinel, in
    # which case it is the base colour.
    Ensures(ToSeq(Result()) == effective_color(ToSeq(base_color), ToSeq(label_color)))
    Ensures(Implies(ToSeq(label_color) == sentinel_inherit(),
                    ToSeq(Result()) == ToSeq(base_color)))
    Ensures(Implies(ToSeq(label_color) != sentinel_inherit(),
                    ToSeq(Result()) == ToSeq(label_color)))
    # post-conditions-end
    # impl-start
    if ToSeq(label_color) == sentinel_inherit():
        tick_color = list(base_color)  # type: List[int]
    else:
        tick_color = list(label_color)
    return tick_color
    # impl-end


def offset_color_secondary(base_color: List[int], label_color: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base_color), 1 / 2))
    Requires(Acc(list_pred(label_color), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base_color), 1 / 2))
    Ensures(Acc(list_pred(label_color), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == effective_color(ToSeq(base_color), ToSeq(label_color)))
    Ensures(Implies(ToSeq(label_color) == sentinel_inherit(),
                    ToSeq(Result()) == ToSeq(base_color)))
    Ensures(Implies(ToSeq(label_color) != sentinel_inherit(),
                    ToSeq(Result()) == ToSeq(label_color)))
    # post-conditions-end
    # impl-start
    if ToSeq(label_color) == sentinel_inherit():
        tick_color = list(base_color)  # type: List[int]
    else:
        tick_color = list(label_color)
    return tick_color
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Instance matplotlib__matplotlib-25287 (nagini). Bundle spec fully pins both offset_color_primary/secondary: postcondition ToSeq(Result()) == effective_color(base,label) plus both Implies clauses cover the ENTIRE input domain (no precondition domain restriction; inputs held read-only at 1/2 fraction so cannot be mutated). effective_color = base if label==sentinel_inherit() else label.

A-LEG AUDIT: meta.json axioms=[] and deep_model_references=[] — there are NO A-legs (G-AX vacuous), consistent with refinement.md §C and mapping.md §3. Verified the sole trust point the R-refinements rest on: Text.set_color/get_color value-identity. Inspected the real repo source inside the eval image (lib/matplotlib/text.py): set_color does `self._color = color` verbatim (only _check_color_like validation, which rejects INVALID names outside the modeled colour-name domain and never transforms a valid value); get_color returns self._color unchanged. So the passthrough is a faithful R-refinement and no library callee carrying behaviour was silently swallowed. Every refinement.md leg is R or I (A1..A6 = R/I at both sites); no kind-3 leg. mapping.md pre-patch note is scoped to the audit view, not the consumer spec (confirmed by same-spec exit 0 for the byte-identical model).

ATTACKS (all byte-identical spec, same-spec exit 0 for all 7; commands: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-25287 <path>`):
- atk_1.py: prepatch bug at PRIMARY site (tick_color=base unconditionally, correct secondary) -> NOT-A-COUNTEREXAMPLE, verification failed (spec caught it). Reproduces the model_prepatch.py bug.
- atk_2.py: return label at BOTH sites (ignore sentinel) -> verification failed (fails on inherit).
- atk_3.py: boundary/off-by-one sentinel PSeq(105,110,104,101,114,105) ('inheri', missing final 't') both sites -> verification failed.
- atk_4.py: control-flow-effect, return [] both sites -> verification failed.
- atk_5.py: inverted branches (label on inherit, base otherwise) both sites -> verification failed.
- atk_6.py: prepatch bug at SECONDARY site (correct primary) -> verification failed. Reproduces model_prepatch_2.py bug.
- atk_7.py: behaviorally-CORRECT echo (chosen = base if inherit else label; tick_color = list(chosen)) both sites -> CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (11.4s).

prepatch_reproduced=true: atk_1 and atk_6 each reproduce one of the two bundled prepatch witnesses (base colour unconditionally) and both FAIL verification — the spec senses the bug at each site independently.

MANDATORY RESOLVE ON THE VERIFYING CANDIDATE (atk_7): materialized its faithful refined patch (atk_7_faithful.patch) — the intermediate `chosen` variable + `list(chosen)` copy refine to value-identity (mapping.md §2), semantically the gold. Ran through the OFFICIAL harness: `cd experiments && python -m swebench_unified.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified --predictions_path preds_atk7.json --run_id sbu-atk7-keeplogs-gvh1c --namespace swebench --instance_image_tag latest ...` (run_id sbu-atk7-keeplogs-gvh1c). RESULT: patch_successfully_applied=True, resolved=True, FAIL_TO_PASS both pass (test_xaxis_offsetText_color, test_yaxis_offsetText_color), all PASS_TO_PASS pass; harness summary 'Instances resolved: 1, errors: 0'. A same-spec verifying impl whose faithful patch RESOLVES is NOT a weakness (echo-of-gold, per G-EQ/G-PANEL-1 resolve policy).

Positive control (pos_control.py = model.py verbatim) verifies (bash scripts/nagini_verify.sh, 10.78s, 'Verification successful').

CONCLUSION: 7 attacks run (6 distinct wrong impls all rejected by verification; 1 correct echo that verifies and whose faithful patch resolves). No verifying-but-incorrect implementation exists — verify DOES imply correct for the tested cases. verify⇏correct NOT exhibited. G-EQ SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-25287.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a secondary annotation that accompanies an axis derives its foreground
  colour from configuration, the colour it should take is the explicitly
  configured label colour. The configured label colour may carry a distinguished
  sentinel value meaning "do not override; defer to the base colour"; in that
  one case, and only that case, the base colour is used instead.

  Formally, for two configured colour values `base_color` and `label_color`
  (each a sequence of code points naming a colour), the effective colour of the
  derived annotation is:

      effective(base_color, label_color)
        = base_color              if label_color is the sentinel `inherit`
        = label_color             otherwise

This rule is applied at two independent configuration sites that differ only in
which pair of base/label colour values they read; both are modelled, each as its
own contracted function, because each is independently observable.

Colour names are modelled as `List[int]` of code points (Nagini bans `str`
indexing); the sentinel `inherit` is the constant code-point sequence for that
word. The result is a fresh sequence whose contents equal the chosen input's
contents. There are no axiomatized callees: the selection is expressed directly.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def sentinel_inherit() -> PSeq[int]:
    # the code points of the word that means "defer to the base colour"
    # i n h e r i t
    return PSeq(105, 110, 104, 101, 114, 105, 116)


@Pure
def effective_color(base_color: PSeq[int], label_color: PSeq[int]) -> PSeq[int]:
    """The colour the derived annotation should take: the explicit label colour,
    except when the label colour is the sentinel, in which case the base
    colour."""
    if label_color == sentinel_inherit():
        return base_color
    return label_color
# pure-end


def offset_color_primary(base_color: List[int], label_color: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base_color), 1 / 2))
    Requires(Acc(list_pred(label_color), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base_color), 1 / 2))
    Ensures(Acc(list_pred(label_color), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The chosen colour is the label colour unless that is the sentinel, in
    # which case it is the base colour.
    Ensures(ToSeq(Result()) == effective_color(ToSeq(base_color), ToSeq(label_color)))
    Ensures(Implies(ToSeq(label_color) == sentinel_inherit(),
                    ToSeq(Result()) == ToSeq(base_color)))
    Ensures(Implies(ToSeq(label_color) != sentinel_inherit(),
                    ToSeq(Result()) == ToSeq(label_color)))
    # post-conditions-end
    # impl-start
    if ToSeq(label_color) == sentinel_inherit():
        tick_color = list(base_color)  # type: List[int]
    else:
        tick_color = list(label_color)
    return tick_color
    # impl-end


def offset_color_secondary(base_color: List[int], label_color: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(base_color), 1 / 2))
    Requires(Acc(list_pred(label_color), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base_color), 1 / 2))
    Ensures(Acc(list_pred(label_color), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == effective_color(ToSeq(base_color), ToSeq(label_color)))
    Ensures(Implies(ToSeq(label_color) == sentinel_inherit(),
                    ToSeq(Result()) == ToSeq(base_color)))
    Ensures(Implies(ToSeq(label_color) != sentinel_inherit(),
                    ToSeq(Result()) == ToSeq(label_color)))
    # post-conditions-end
    # impl-start
    if ToSeq(label_color) == sentinel_inherit():
        tick_color = list(base_color)  # type: List[int]
    else:
        tick_color = list(label_color)
    return tick_color
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Instance matplotlib__matplotlib-25287 (nagini). Bundle spec fully pins both offset_color_primary/secondary: postcondition ToSeq(Result()) == effective_color(base,label) plus both Implies clauses cover the ENTIRE input domain (no precondition domain restriction; inputs held read-only at 1/2 fraction so cannot be mutated). effective_color = base if label==sentinel_inherit() else label.

A-LEG AUDIT: meta.json axioms=[] and deep_model_references=[] — there are NO A-legs (G-AX vacuous), consistent with refinement.md §C and mapping.md §3. Verified the sole trust point the R-refinements rest on: Text.set_color/get_color value-identity. Inspected the real repo source inside the eval image (lib/matplotlib/text.py): set_color does `self._color = color` verbatim (only _check_color_like validation, which rejects INVALID names outside the modeled colour-name domain and never transforms a valid value); get_color returns self._color unchanged. So the passthrough is a faithful R-refinement and no library callee carrying behaviour was silently swallowed. Every refinement.md leg is R or I (A1..A6 = R/I at both sites); no kind-3 leg. mapping.md pre-patch note is scoped to the audit view, not the consumer spec (confirmed by same-spec exit 0 for the byte-identical model).

ATTACKS (all byte-identical spec, same-spec exit 0 for all 7; commands: `python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-25287 <path>`):
- atk_1.py: prepatch bug at PRIMARY site (tick_color=base unconditionally, correct secondary) -> NOT-A-COUNTEREXAMPLE, verification failed (spec caught it). Reproduces the model_prepatch.py bug.
- atk_2.py: return label at BOTH sites (ignore sentinel) -> verification failed (fails on inherit).
- atk_3.py: boundary/off-by-one sentinel PSeq(105,110,104,101,114,105) ('inheri', missing final 't') both sites -> verification failed.
- atk_4.py: control-flow-effect, return [] both sites -> verification failed.
- atk_5.py: inverted branches (label on inherit, base otherwise) both sites -> verification failed.
- atk_6.py: prepatch bug at SECONDARY site (correct primary) -> verification failed. Reproduces model_prepatch_2.py bug.
- atk_7.py: behaviorally-CORRECT echo (chosen = base if inherit else label; tick_color = list(chosen)) both sites -> CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies (11.4s).

prepatch_reproduced=true: atk_1 and atk_6 each reproduce one of the two bundled prepatch witnesses (base colour unconditionally) and both FAIL verification — the spec senses the bug at each site independently.

MANDATORY RESOLVE ON THE VERIFYING CANDIDATE (atk_7): materialized its faithful refined patch (atk_7_faithful.patch) — the intermediate `chosen` variable + `list(chosen)` copy refine to value-identity (mapping.md §2), semantically the gold. Ran through the OFFICIAL harness: `cd experiments && python -m swebench_unified.run_evaluation --dataset_name princeton-nlp/SWE-bench_Verified --predictions_path preds_atk7.json --run_id sbu-atk7-keeplogs-gvh1c --namespace swebench --instance_image_tag latest ...` (run_id sbu-atk7-keeplogs-gvh1c). RESULT: patch_successfully_applied=True, resolved=True, FAIL_TO_PASS both pass (test_xaxis_offsetText_color, test_yaxis_offsetText_color), all PASS_TO_PASS pass; harness summary 'Instances resolved: 1, errors: 0'. A same-spec verifying impl whose faithful patch RESOLVES is NOT a weakness (echo-of-gold, per G-EQ/G-PANEL-1 resolve policy).

Positive control (pos_control.py = model.py verbatim) verifies (bash scripts/nagini_verify.sh, 10.78s, 'Verification successful').

CONCLUSION: 7 attacks run (6 distinct wrong impls all rejected by verification; 1 correct echo that verifies and whose faithful patch resolves). No verifying-but-incorrect implementation exists — verify DOES imply correct for the tested cases. verify⇏correct NOT exhibited. G-EQ SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The modeled functions offset_color_primary/offset_color_secondary agree with the real patched repo on every input in the bridgeable domain; the spec is neither too strong nor drifted.

Evidence:
1. Model verifies under the pinned Nagini verifier (exit 0, 13.05 s).
2. The bundle models the REAL gold patch for matplotlib__matplotlib-25287 (tick-label-color inheritance at lib/matplotlib/axis.py XAxis._init / YAxis._init), matching data/swe_bench_verified test.jsonl and meta.json patch_diff. (Note: a stray gold.patch about text antialiasing found in one dir belongs to a DIFFERENT matplotlib instance and is irrelevant to this bundle.)
3. Spec = effective_color(base,label) = base if label==sentinel_inherit() (code points of 'inherit') else label, applied at both sites. This is a byte-for-byte behavioral mirror of the gold hunk `if rcParams['<axis>tick.labelcolor']=='inherit': tick_color=rcParams['<axis>tick.color'] else rcParams['<axis>tick.labelcolor']`; type refinement is str<->List[int] code points (mapping.md §2), and Text.set(color=v)/get_color() is a verbatim value passthrough (confirmed against the F2P tests test_xaxis/yaxis_offsetText_color).
4. Recorded G-CONF ran shadow-vs-real-patched-repo over 104,220 site-inputs (110 boundary pairs + 52,000 fuzz, seed 25287) with 0 disagreements (status pass).
5. Independent check: compared the spec's selection against the real patched selection over 200,000 random inputs (named colors, hex w/ and w/o alpha, grayscale, single-letter shorthands, the sentinel) — 0 disagreements. rcParams canonicalization is accounted for: model inputs are the values read back from rcParams, exactly what the modeled site reads.
6. G-DIFF pass: both prepatch witnesses (unconditional base color) fail the postcondition, so the spec senses the real bug at each site — not vacuously strong.

No input exists where the spec disagrees with the real callee. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The public problem_statement already contains the full gold fix logic verbatim: it quotes the reporter's patch `color=mpl.rcParams['xtick.color'] if mpl.rcParams['xtick.labelcolor']=='inherit' else mpl.rcParams['xtick.labelcolor']` for both x and y sites, naming the 'inherit' sentinel, the base color (tick.color), and the label color (tick.labelcolor). The spec view (model.py) exposes exactly this and nothing more, abstracted: sentinel_inherit() and effective_color(base_color, label_color) = base_color if label_color==inherit else label_color, modeled at two independent contracted sites (offset_color_primary/secondary), with colours abstracted to List[int] code points. Every notion in the spec — the inherit sentinel, preferring label over base colour, the two-site structure — is drawn from the public problem_statement; no gold-patch specific (file path lib/matplotlib/axis.py, the tick_color local-variable refactor, offsetText.set call) leaks beyond it. refinement.md/mapping.md were reviewed for the same and add no gold-specific detail beyond the public statement. Therefore no leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
