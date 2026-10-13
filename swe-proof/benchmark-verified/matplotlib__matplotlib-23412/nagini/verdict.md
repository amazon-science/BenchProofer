# P2 adversarial audit — matplotlib__matplotlib-23412

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -41,7 +40,6 @@
 def render_dash_pattern(phase: int, onoff: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(onoff), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The stored on/off sequence is read-only: it is returned at the same
@@ -60,7 +58,7 @@
     Ensures(Result()[0] == phase)
     # post-conditions-end
     # impl-start
-    result = [phase]  # type: List[int]
+    result = [0]  # type: List[int]
     i = 0
     while i < len(onoff):
         # invariants-start
@@ -69,8 +67,7 @@
         Invariant(0 <= i and i <= len(onoff))
         Invariant(len(result) == i + 1)
         Invariant(ToSeq(onoff) == Old(ToSeq(onoff)))
-        Invariant(ToSeq(result) == PSeq(phase) + ToSeq(onoff).take(i))
-        Invariant(MustTerminate(len(onoff) - i + 1))
+        Invariant(ToSeq(result) == PSeq(0) + ToSeq(onoff).take(i))
         # invariants-end
         Assert(ToSeq(onoff).take(i + 1) == ToSeq(onoff).take(i) + PSeq(onoff[i]))
         result.append(onoff[i])
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -41,7 +40,6 @@
 def render_dash_pattern(phase: int, onoff: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(onoff), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The stored on/off sequence is read-only: it is returned at the same
@@ -60,7 +58,7 @@
     Ensures(Result()[0] == phase)
     # post-conditions-end
     # impl-start
-    result = [phase]  # type: List[int]
+    result = [phase + 1]  # type: List[int]
     i = 0
     while i < len(onoff):
         # invariants-start
@@ -69,8 +67,7 @@
         Invariant(0 <= i and i <= len(onoff))
         Invariant(len(result) == i + 1)
         Invariant(ToSeq(onoff) == Old(ToSeq(onoff)))
-        Invariant(ToSeq(result) == PSeq(phase) + ToSeq(onoff).take(i))
-        Invariant(MustTerminate(len(onoff) - i + 1))
+        Invariant(ToSeq(result) == PSeq(phase + 1) + ToSeq(onoff).take(i))
         # invariants-end
         Assert(ToSeq(onoff).take(i + 1) == ToSeq(onoff).take(i) + PSeq(onoff[i]))
         result.append(onoff[i])
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -41,7 +40,6 @@
 def render_dash_pattern(phase: int, onoff: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(onoff), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The stored on/off sequence is read-only: it is returned at the same
@@ -61,20 +59,15 @@
     # post-conditions-end
     # impl-start
     result = [phase]  # type: List[int]
-    i = 0
+    i = 1
     while i < len(onoff):
         # invariants-start
         Invariant(Acc(list_pred(onoff), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(onoff))
-        Invariant(len(result) == i + 1)
+        Invariant(1 <= i and i <= len(onoff))
         Invariant(ToSeq(onoff) == Old(ToSeq(onoff)))
-        Invariant(ToSeq(result) == PSeq(phase) + ToSeq(onoff).take(i))
-        Invariant(MustTerminate(len(onoff) - i + 1))
         # invariants-end
-        Assert(ToSeq(onoff).take(i + 1) == ToSeq(onoff).take(i) + PSeq(onoff[i]))
         result.append(onoff[i])
         i = i + 1
-    Assert(ToSeq(onoff).take(len(onoff)) == ToSeq(onoff))
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -41,7 +40,6 @@
 def render_dash_pattern(phase: int, onoff: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(onoff), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The stored on/off sequence is read-only: it is returned at the same
@@ -61,20 +59,18 @@
     # post-conditions-end
     # impl-start
     result = [phase]  # type: List[int]
+    n = len(onoff)
     i = 0
-    while i < len(onoff):
+    while i < n:
         # invariants-start
         Invariant(Acc(list_pred(onoff), 1 / 2))
         Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(onoff))
+        Invariant(0 <= i and i <= n)
+        Invariant(n == len(onoff))
         Invariant(len(result) == i + 1)
         Invariant(ToSeq(onoff) == Old(ToSeq(onoff)))
-        Invariant(ToSeq(result) == PSeq(phase) + ToSeq(onoff).take(i))
-        Invariant(MustTerminate(len(onoff) - i + 1))
         # invariants-end
-        Assert(ToSeq(onoff).take(i + 1) == ToSeq(onoff).take(i) + PSeq(onoff[i]))
-        result.append(onoff[i])
+        result.append(onoff[n - 1 - i])
         i = i + 1
-    Assert(ToSeq(onoff).take(len(onoff)) == ToSeq(onoff))
     return result
     # impl-end
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -41,7 +40,6 @@
 def render_dash_pattern(phase: int, onoff: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(onoff), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The stored on/off sequence is read-only: it is returned at the same
@@ -60,6 +58,7 @@
     Ensures(Result()[0] == phase)
     # post-conditions-end
     # impl-start
+    onoff.append(phase)
     result = [phase]  # type: List[int]
     i = 0
     while i < len(onoff):
@@ -70,7 +69,6 @@
         Invariant(len(result) == i + 1)
         Invariant(ToSeq(onoff) == Old(ToSeq(onoff)))
         Invariant(ToSeq(result) == PSeq(phase) + ToSeq(onoff).take(i))
-        Invariant(MustTerminate(len(onoff) - i + 1))
         # invariants-end
         Assert(ToSeq(onoff).take(i + 1) == ToSeq(onoff).take(i) + PSeq(onoff[i]))
         result.append(onoff[i])
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -41,7 +40,6 @@
 def render_dash_pattern(phase: int, onoff: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(onoff), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The stored on/off sequence is read-only: it is returned at the same
@@ -60,21 +58,6 @@
     Ensures(Result()[0] == phase)
     # post-conditions-end
     # impl-start
-    result = [phase]  # type: List[int]
-    i = 0
-    while i < len(onoff):
-        # invariants-start
-        Invariant(Acc(list_pred(onoff), 1 / 2))
-        Invariant(Acc(list_pred(result)))
-        Invariant(0 <= i and i <= len(onoff))
-        Invariant(len(result) == i + 1)
-        Invariant(ToSeq(onoff) == Old(ToSeq(onoff)))
-        Invariant(ToSeq(result) == PSeq(phase) + ToSeq(onoff).take(i))
-        Invariant(MustTerminate(len(onoff) - i + 1))
-        # invariants-end
-        Assert(ToSeq(onoff).take(i + 1) == ToSeq(onoff).take(i) + PSeq(onoff[i]))
-        result.append(onoff[i])
-        i = i + 1
-    Assert(ToSeq(onoff).take(len(onoff)) == ToSeq(onoff))
+    result = onoff  # type: List[int]
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -27,7 +27,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -41,7 +40,6 @@
 def render_dash_pattern(phase: int, onoff: List[int]) -> List[int]:
     # pre-conditions-start
     Requires(Acc(list_pred(onoff), 1 / 2))
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     # The stored on/off sequence is read-only: it is returned at the same
@@ -70,11 +68,11 @@
         Invariant(len(result) == i + 1)
         Invariant(ToSeq(onoff) == Old(ToSeq(onoff)))
         Invariant(ToSeq(result) == PSeq(phase) + ToSeq(onoff).take(i))
-        Invariant(MustTerminate(len(onoff) - i + 1))
         # invariants-end
         Assert(ToSeq(onoff).take(i + 1) == ToSeq(onoff).take(i) + PSeq(onoff[i]))
         result.append(onoff[i])
         i = i + 1
-    Assert(ToSeq(onoff).take(len(onoff)) == ToSeq(onoff))
+    if len(onoff) > 0:
+        result.append(onoff[len(onoff) - 1])
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-23412.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A filled outline shape stores its boundary stroke style as a dash pattern: a
  scalar phase (the starting position along the on/off cycle) together with the
  even-length on/off ink-length sequence. When the shape is rendered, the dash
  pattern handed to the drawing back end must be the shape's OWN dash pattern:
  its phase is preserved exactly, and the on/off sequence is preserved exactly.

  In particular, two shapes whose stored dash patterns differ only in their
  phase must be handed dash patterns that still differ in that same phase; the
  phase a caller supplies is honoured.

The phase and the on/off ink lengths are modelled as integers (the tested
behaviour is whether the stored phase is carried through to the renderer
exactly -- this is independent of any floating-point magnitude, so an exact
integer carrier is faithful; see mapping.md). The dash pattern handed to the
renderer is modelled as a single `List[int]` whose head element is the phase
passed to the back end and whose tail is the on/off sequence passed to the
back end.

There are no axiomatized callees: the modelled behaviour is a pure
construction of the render-time dash pattern from the stored one.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
# pure-end


def render_dash_pattern(phase: int, onoff: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(onoff), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # The stored on/off sequence is read-only: it is returned at the same
    # fractional permission it was required at, unmutated.
    Ensures(Acc(list_pred(onoff), 1 / 2))
    Ensures(ToSeq(onoff) == Old(ToSeq(onoff)))
    # The render-time pattern is freshly owned and never shorter than its head.
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(onoff) + 1)
    Ensures(len(Result()) >= 1)
    # The phase handed to the renderer equals the stored phase exactly,
    # followed by the stored on/off sequence element-for-element in order. This
    # pins both the discriminating phase clause (a shape with a nonzero stored
    # phase must be rendered with that same phase) and the on/off passthrough.
    Ensures(ToSeq(Result()) == PSeq(phase) + Old(ToSeq(onoff)))
    Ensures(Result()[0] == phase)
    # post-conditions-end
    # impl-start
    result = [phase]  # type: List[int]
    i = 0
    while i < len(onoff):
        # invariants-start
        Invariant(Acc(list_pred(onoff), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(onoff))
        Invariant(len(result) == i + 1)
        Invariant(ToSeq(onoff) == Old(ToSeq(onoff)))
        Invariant(ToSeq(result) == PSeq(phase) + ToSeq(onoff).take(i))
        # invariants-end
        Assert(ToSeq(onoff).take(i + 1) == ToSeq(onoff).take(i) + PSeq(onoff[i]))
        result.append(onoff[i])
        i = i + 1
    Assert(ToSeq(onoff).take(len(onoff)) == ToSeq(onoff))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle matplotlib__matplotlib-23412 nagini. Spec pins Result() completely: Ensures(ToSeq(Result())==PSeq(phase)+Old(ToSeq(onoff))) AND Result()[0]==phase AND len(Result())==len(onoff)+1 AND len>=1, with onoff held READ-ONLY at Acc(list_pred(onoff),1/2) both required and ensured, plus ToSeq(onoff)==Old(ToSeq(onoff)). That is a full functional pin of the output as [phase]+onoff with an unmodifiable input — zero degrees of freedom.

All attacks confirmed same-spec via `same-spec` (exit 0, byte-identical spec signature) before verifying.

Positive control atk_pos.py (= bundle model.py verbatim, diff IDENTICAL): weakness EXIT=0 CANDIDATE, verifies 13.8s.

7 distinct wrong impls, all editing ONLY the impl region:
- atk_1.py PREPATCH bug (result=[0], phase dropped): weakness EXIT=2, 'attack does not verify (verification failed)'. => prepatch_reproduced=true (fails postcondition ToSeq(Result())==PSeq(phase)+... and Result()[0]==phase when phase!=0 — G-DIFF holds).
- atk_2.py ungrounded/off-by-one on phase carrier (result=[phase+1]): EXIT=2, does not verify.
- atk_3.py boundary/off-by-one (skip first onoff element, length short by 1): EXIT=2, does not verify.
- atk_4.py control-flow-effect (on/off appended in reverse index order): EXIT=2, does not verify.
- atk_5.py control-flow-effect (mutate read-only onoff via onoff.append): EXIT=2, does not verify — the Acc(...,1/2) read-only permission + ToSeq(onoff)==Old(ToSeq(onoff)) rejects mutation.
- atk_6.py ungrounded-oracle echo (return onoff aliased as result, no phase head, no fresh ownership): EXIT=2, does not verify.
- atk_7.py partial-domain (correct on empty onoff, duplicated tail element otherwise): EXIT=2, does not verify — violates len(Result())==len(onoff)+1.

NO attack came back CANDIDATE, so there was NO faithful refined patch to materialize/run through run_resolve. The only verifying same-spec impl is the gold model itself.

refinement.md / mapping.md A-leg audit: axioms region is EMPTY, model.py has 0 @ContractOnly, and NO axiom_check.py exists — consistent with mapping.md §3 (the changed expression is pure tuple construction from self._dash_pattern[0]/[1] with no callee provenance). Therefore there are NO A-consumed and NO A-reference legs; every leg is R (A1 offset float↔int; A2 onoffseq↔List[int]) or R+I (A3 construction). No kind-3 (unexpressible-changed-op) leg. Gold patch.diff matches refinement.md §A verbatim: `_dash_pattern=(0, self._dash_pattern[1])` (offset forced 0) -> `_dash_pattern=(self._dash_pattern)` (offset preserved); the discriminating change (offset component 0 -> self._dash_pattern[0]) is modeled directly and concretely as Result()[0]==phase, not hidden behind an axiom. The prepatch attack (atk_1) falsifying exactly this clause confirms the model↔patch correspondence senses the change.

Verdict: SOUND — ≥5 (7) distinct wrong impls run through the official adversary weakness check plus prepatch, none verified; the sole verifying same-spec impl is the gold model; spec fully pins the tested behaviour (offset passthrough + on/off passthrough + read-only input). verify⇒correct holds for this frozen spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `atk_pos.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-23412.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A filled outline shape stores its boundary stroke style as a dash pattern: a
  scalar phase (the starting position along the on/off cycle) together with the
  even-length on/off ink-length sequence. When the shape is rendered, the dash
  pattern handed to the drawing back end must be the shape's OWN dash pattern:
  its phase is preserved exactly, and the on/off sequence is preserved exactly.

  In particular, two shapes whose stored dash patterns differ only in their
  phase must be handed dash patterns that still differ in that same phase; the
  phase a caller supplies is honoured.

The phase and the on/off ink lengths are modelled as integers (the tested
behaviour is whether the stored phase is carried through to the renderer
exactly -- this is independent of any floating-point magnitude, so an exact
integer carrier is faithful; see mapping.md). The dash pattern handed to the
renderer is modelled as a single `List[int]` whose head element is the phase
passed to the back end and whose tail is the on/off sequence passed to the
back end.

There are no axiomatized callees: the modelled behaviour is a pure
construction of the render-time dash pattern from the stored one.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
# pure-end


def render_dash_pattern(phase: int, onoff: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(onoff), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    # The stored on/off sequence is read-only: it is returned at the same
    # fractional permission it was required at, unmutated.
    Ensures(Acc(list_pred(onoff), 1 / 2))
    Ensures(ToSeq(onoff) == Old(ToSeq(onoff)))
    # The render-time pattern is freshly owned and never shorter than its head.
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == len(onoff) + 1)
    Ensures(len(Result()) >= 1)
    # The phase handed to the renderer equals the stored phase exactly,
    # followed by the stored on/off sequence element-for-element in order. This
    # pins both the discriminating phase clause (a shape with a nonzero stored
    # phase must be rendered with that same phase) and the on/off passthrough.
    Ensures(ToSeq(Result()) == PSeq(phase) + Old(ToSeq(onoff)))
    Ensures(Result()[0] == phase)
    # post-conditions-end
    # impl-start
    result = [phase]  # type: List[int]
    i = 0
    while i < len(onoff):
        # invariants-start
        Invariant(Acc(list_pred(onoff), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(onoff))
        Invariant(len(result) == i + 1)
        Invariant(ToSeq(onoff) == Old(ToSeq(onoff)))
        Invariant(ToSeq(result) == PSeq(phase) + ToSeq(onoff).take(i))
        # invariants-end
        Assert(ToSeq(onoff).take(i + 1) == ToSeq(onoff).take(i) + PSeq(onoff[i]))
        result.append(onoff[i])
        i = i + 1
    Assert(ToSeq(onoff).take(len(onoff)) == ToSeq(onoff))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle matplotlib__matplotlib-23412 nagini. Spec pins Result() completely: Ensures(ToSeq(Result())==PSeq(phase)+Old(ToSeq(onoff))) AND Result()[0]==phase AND len(Result())==len(onoff)+1 AND len>=1, with onoff held READ-ONLY at Acc(list_pred(onoff),1/2) both required and ensured, plus ToSeq(onoff)==Old(ToSeq(onoff)). That is a full functional pin of the output as [phase]+onoff with an unmodifiable input — zero degrees of freedom.

All attacks confirmed same-spec via `same-spec` (exit 0, byte-identical spec signature) before verifying.

Positive control atk_pos.py (= bundle model.py verbatim, diff IDENTICAL): weakness EXIT=0 CANDIDATE, verifies 13.8s.

7 distinct wrong impls, all editing ONLY the impl region:
- atk_1.py PREPATCH bug (result=[0], phase dropped): weakness EXIT=2, 'attack does not verify (verification failed)'. => prepatch_reproduced=true (fails postcondition ToSeq(Result())==PSeq(phase)+... and Result()[0]==phase when phase!=0 — G-DIFF holds).
- atk_2.py ungrounded/off-by-one on phase carrier (result=[phase+1]): EXIT=2, does not verify.
- atk_3.py boundary/off-by-one (skip first onoff element, length short by 1): EXIT=2, does not verify.
- atk_4.py control-flow-effect (on/off appended in reverse index order): EXIT=2, does not verify.
- atk_5.py control-flow-effect (mutate read-only onoff via onoff.append): EXIT=2, does not verify — the Acc(...,1/2) read-only permission + ToSeq(onoff)==Old(ToSeq(onoff)) rejects mutation.
- atk_6.py ungrounded-oracle echo (return onoff aliased as result, no phase head, no fresh ownership): EXIT=2, does not verify.
- atk_7.py partial-domain (correct on empty onoff, duplicated tail element otherwise): EXIT=2, does not verify — violates len(Result())==len(onoff)+1.

NO attack came back CANDIDATE, so there was NO faithful refined patch to materialize/run through run_resolve. The only verifying same-spec impl is the gold model itself.

refinement.md / mapping.md A-leg audit: axioms region is EMPTY, model.py has 0 @ContractOnly, and NO axiom_check.py exists — consistent with mapping.md §3 (the changed expression is pure tuple construction from self._dash_pattern[0]/[1] with no callee provenance). Therefore there are NO A-consumed and NO A-reference legs; every leg is R (A1 offset float↔int; A2 onoffseq↔List[int]) or R+I (A3 construction). No kind-3 (unexpressible-changed-op) leg. Gold patch.diff matches refinement.md §A verbatim: `_dash_pattern=(0, self._dash_pattern[1])` (offset forced 0) -> `_dash_pattern=(self._dash_pattern)` (offset preserved); the discriminating change (offset component 0 -> self._dash_pattern[0]) is modeled directly and concretely as Result()[0]==phase, not hidden behind an axiom. The prepatch attack (atk_1) falsifying exactly this clause confirms the model↔patch correspondence senses the change.

Verdict: SOUND — ≥5 (7) distinct wrong impls run through the official adversary weakness check plus prepatch, none verified; the sole verifying same-spec impl is the gold model; spec fully pins the tested behaviour (offset passthrough + on/off passthrough + read-only input). verify⇒correct holds for this frozen spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness verified for matplotlib__matplotlib-23412 nagini bundle (render_dash_pattern models the offset-preservation fix in Patch.draw / lib/matplotlib/patches.py). 

### Checks performed
1. Discriminating semantics faithful. Gold fix: cbook._setattr_cm installed value changes from (0, self._dash_pattern[1]) [offset zeroed] to (self._dash_pattern) [offset preserved]; consumed by gc.set_dashes(*self._dash_pattern) at patches.py:552. Model pins this via Result()[0]==phase and ToSeq(Result())==PSeq(phase)+Old(ToSeq(onoff)). Empirically ran the REAL patched Patch.draw (installed mpl 3.6.3 already contains the post-fix code; also confirmed identical patched code worktree at base_commit f06c2c3 + gold patch) via a capturing RendererBase: real hands->model[6,10,10],->[0,10,10],->[6],->[-6,5,0],->[3,1,2,3] — all match head-for-head, tail-for-tail.
2. Ran the bundle's conformance_check.py against the real callee: 'G-CONF OK ... 100338 inputs (338 boundary + 100000 fuzz, seed 23412), 0 disagreements', exit 0.
3. Model verifies: nagini_verify.sh -> 'Verification successful' (10.95s). G-DIFF: model_prepatch.py fails whenever phase!=0 (spec senses the change). F2P test exercises phase=6!=0.

SPEC IS NOT TOO STRONG: The only real-vs-model divergences are on inputs OUTSIDE the reachable/modeled domain. For onoff=[-1] or onoff=[0,0] (admitted by the model precondition Acc(list_pred(onoff),1/2)) the real gc.set_dashes raises ValueError (non-negative / at-least-one-positive), while the model returns [0,-1]/[0,0,0]. These are NOT genuine callee disagreements: the stored _dash_pattern in the repo is always produced by _scale_dashes(_get_dash_pattern(...)) which yields validated non-negative sequences with >=1 positive element (lines.py:32,62). Such degenerate stored patterns are unreachable repo states, and mapping.md/conformance_check.py scope the domain to exactly the reachable non-negative on/off sequences. No diverging input exists on the real repo's reachable state space. The float<->int offset abstraction is value-exact for integer offsets (tested), and the None<->empty-list solid bridge is exercised and agrees.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region confirmed byte-identical (same-spec exit 0; region_hashes match). Mechanical leakage.screen (nagini/python flavor) over spec_view(model.py) PASSES with zero hard failures: no diff markers, no reproduced gold line (>=8 chars), no patched file path (lib/matplotlib/patches.py), no spec-view identifier/comment echoing a patched repo symbol (draw, _dash_pattern, cbook._setattr_cm, gc.set_dashes), no bug/fix narration terms.

Substantive judgment vs the SOLVER-VISIBLE problem_statement only (hints_text explicitly excluded): the public bug report already states the entire behavioral goal — '[Bug]: offset dash linestyle has no effect in patch objects', 'When setting the linestyle on a patch object using a dash tuple the offset has no effect', with an Expected outcome that patch edges honor the dash offset (phase shift) exactly like Line2D, and a reproduction comparing offset 0 vs offset 10 with the same on/off tuple. The spec view (docstring + Ensures) merely restates this desired behavior abstractly over 'a filled outline shape': the render-time dash pattern preserves the shape's OWN phase (Result()[0] == phase) and on/off sequence (ToSeq(Result()) == PSeq(phase) + Old(ToSeq(onoff))), and two patterns differing only in phase stay differing — i.e. the public expected outcome, not the edit.

No edit-site localization is disclosed: no changed file, no repo symbols, and no hint of the pre-patch mechanism (offset forced to 0 via the (0, self._dash_pattern[1]) install). The generic pure-construction framing render_dash_pattern(phase, onoff) -> List[int] gives a solver no more than the bug report does. mapping.md / refinement.md / model_prepatch.py are auditor-side artifacts, not part of the consumer spec view (spec_view projects model.py only). 

IMPORTANT: the exact fix ('replacing the 0 here with the passed offset', with the patches.py:590 line link) appears ONLY in hints_text, which is correctly out of scope for the leakage screen; the spec view does not reproduce that content. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `model.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
