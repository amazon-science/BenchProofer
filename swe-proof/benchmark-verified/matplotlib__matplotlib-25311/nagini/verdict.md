# P2 adversarial audit — matplotlib__matplotlib-25311

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py` |
| does not verify against this specification, so the specification excludes it | 5 | `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying wrong-impl whose faithful refined patch fails to resolve was found. The 5 verifying candidates (atk_1..atk_5) are behavioural ECHOES of the gold: the model impl only controls the returned List[int] modelling the helper __dict__ object identities. The frozen postconditions force ALL 5 genuine attrs present and surface (canvas) absent; the frozen preconditions ground distinctness (surface != each attr) for exactly the 5 attrs, so an impl can neither drop a genuine attr, include the canvas, nor add an ungrounded extra element and still verify. The only degrees of freedom that verify are reordering and duplication of the 5 genuine attrs (atk_1 reversed; atk_2/3/4/5 duplicate an attr). Both are invisible in the real refinement: __dict__ insertion order is not observable to the F2P test (which only asserts no 'FigureCanvas' name appears in pickletools.genops of the figure pickle stream), and an attribute cannot be 'duplicated' in a real __dict__ (re-assignment is idempotent). Hence the faithful refined patch for every candidate is the gold patch (remove stored self.canvas; keep the class-level canvas=property; retain genuine attrs) — which RESOLVES.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     Requires(surface != blit_flag)
     Requires(surface != cid_pick)
     Requires(surface != cid_release)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -88,49 +86,35 @@
     Ensures(contains(ToSeq(Result()), cid_release))
     # post-conditions-end
     # impl-start
-    # The serialisable state holds the genuine helper attributes; the drawing
-    # surface is obtained on demand (read_surface) rather than stored.
-    state = [element_id, drag_flag, blit_flag,
-             cid_pick, cid_release]  # type: List[int]
-    # The sequence view of the literal state, spelled out so the front-recursive
-    # membership predicate unfolds one element per step.
+    state = [cid_release, cid_pick, blit_flag, drag_flag, element_id]  # type: List[int]
     s = ToSeq(state)  # type: PSeq[int]
     Assert(len(s) == 5)
-    Assert(s[0] == element_id)
-    Assert(s[1] == drag_flag)
-    Assert(s[2] == blit_flag)
-    Assert(s[3] == cid_pick)
-    Assert(s[4] == cid_release)
-    Assert(s.drop(1)[0] == drag_flag)
+    Assert(s.drop(0)[0] == cid_release)
+    Assert(s.drop(1)[0] == cid_pick)
     Assert(s.drop(2)[0] == blit_flag)
-    Assert(s.drop(3)[0] == cid_pick)
-    Assert(s.drop(4)[0] == cid_release)
+    Assert(s.drop(3)[0] == drag_flag)
+    Assert(s.drop(4)[0] == element_id)
     Assert(len(s.drop(5)) == 0)
-    # The drawing surface is absent: prove `not contains(..., surface)` from the
-    # empty tail upward, each step discharging `head != surface` from the
-    # distinctness preconditions.
     Assert(not contains(s.drop(5), surface))
     Assert(not contains(s.drop(4), surface))
     Assert(not contains(s.drop(3), surface))
     Assert(not contains(s.drop(2), surface))
     Assert(not contains(s.drop(1), surface))
-    Assert(not contains(s, surface))
-    # Each genuine attribute IS present: prove `contains` at its position by
-    # unfolding to the element it sits at.
-    Assert(contains(s, element_id))
+    Assert(not contains(s.drop(0), surface))
+    Assert(contains(s.drop(4), element_id))
+    Assert(contains(s.drop(3), element_id))
+    Assert(contains(s.drop(2), element_id))
+    Assert(contains(s.drop(1), element_id))
+    Assert(contains(s.drop(0), element_id))
+    Assert(contains(s.drop(3), drag_flag))
+    Assert(contains(s.drop(2), drag_flag))
     Assert(contains(s.drop(1), drag_flag))
-    Assert(contains(s, drag_flag))
+    Assert(contains(s.drop(0), drag_flag))
     Assert(contains(s.drop(2), blit_flag))
     Assert(contains(s.drop(1), blit_flag))
-    Assert(contains(s, blit_flag))
-    Assert(contains(s.drop(3), cid_pick))
-    Assert(contains(s.drop(2), cid_pick))
+    Assert(contains(s.drop(0), blit_flag))
     Assert(contains(s.drop(1), cid_pick))
-    Assert(contains(s, cid_pick))
-    Assert(contains(s.drop(4), cid_release))
-    Assert(contains(s.drop(3), cid_release))
-    Assert(contains(s.drop(2), cid_release))
-    Assert(contains(s.drop(1), cid_release))
-    Assert(contains(s, cid_release))
+    Assert(contains(s.drop(0), cid_pick))
+    Assert(contains(s.drop(0), cid_release))
     return state
     # impl-end
```

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     Requires(surface != blit_flag)
     Requires(surface != cid_pick)
     Requires(surface != cid_release)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -88,49 +86,37 @@
     Ensures(contains(ToSeq(Result()), cid_release))
     # post-conditions-end
     # impl-start
-    # The serialisable state holds the genuine helper attributes; the drawing
-    # surface is obtained on demand (read_surface) rather than stored.
-    state = [element_id, drag_flag, blit_flag,
-             cid_pick, cid_release]  # type: List[int]
-    # The sequence view of the literal state, spelled out so the front-recursive
-    # membership predicate unfolds one element per step.
+    state = [element_id, drag_flag, blit_flag, cid_pick, cid_release, element_id]  # type: List[int]
     s = ToSeq(state)  # type: PSeq[int]
-    Assert(len(s) == 5)
-    Assert(s[0] == element_id)
-    Assert(s[1] == drag_flag)
-    Assert(s[2] == blit_flag)
-    Assert(s[3] == cid_pick)
-    Assert(s[4] == cid_release)
+    Assert(len(s) == 6)
+    Assert(s.drop(0)[0] == element_id)
     Assert(s.drop(1)[0] == drag_flag)
     Assert(s.drop(2)[0] == blit_flag)
     Assert(s.drop(3)[0] == cid_pick)
     Assert(s.drop(4)[0] == cid_release)
-    Assert(len(s.drop(5)) == 0)
-    # The drawing surface is absent: prove `not contains(..., surface)` from the
-    # empty tail upward, each step discharging `head != surface` from the
-    # distinctness preconditions.
+    Assert(s.drop(5)[0] == element_id)
+    Assert(len(s.drop(6)) == 0)
+    Assert(not contains(s.drop(6), surface))
     Assert(not contains(s.drop(5), surface))
     Assert(not contains(s.drop(4), surface))
     Assert(not contains(s.drop(3), surface))
     Assert(not contains(s.drop(2), surface))
     Assert(not contains(s.drop(1), surface))
-    Assert(not contains(s, surface))
-    # Each genuine attribute IS present: prove `contains` at its position by
-    # unfolding to the element it sits at.
-    Assert(contains(s, element_id))
+    Assert(not contains(s.drop(0), surface))
+    Assert(contains(s.drop(0), element_id))
     Assert(contains(s.drop(1), drag_flag))
-    Assert(contains(s, drag_flag))
+    Assert(contains(s.drop(0), drag_flag))
     Assert(contains(s.drop(2), blit_flag))
     Assert(contains(s.drop(1), blit_flag))
-    Assert(contains(s, blit_flag))
+    Assert(contains(s.drop(0), blit_flag))
     Assert(contains(s.drop(3), cid_pick))
     Assert(contains(s.drop(2), cid_pick))
     Assert(contains(s.drop(1), cid_pick))
-    Assert(contains(s, cid_pick))
+    Assert(contains(s.drop(0), cid_pick))
     Assert(contains(s.drop(4), cid_release))
     Assert(contains(s.drop(3), cid_release))
     Assert(contains(s.drop(2), cid_release))
     Assert(contains(s.drop(1), cid_release))
-    Assert(contains(s, cid_release))
+    Assert(contains(s.drop(0), cid_release))
     return state
     # impl-end
```

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     Requires(surface != blit_flag)
     Requires(surface != cid_pick)
     Requires(surface != cid_release)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -88,49 +86,39 @@
     Ensures(contains(ToSeq(Result()), cid_release))
     # post-conditions-end
     # impl-start
-    # The serialisable state holds the genuine helper attributes; the drawing
-    # surface is obtained on demand (read_surface) rather than stored.
-    state = [element_id, drag_flag, blit_flag,
-             cid_pick, cid_release]  # type: List[int]
-    # The sequence view of the literal state, spelled out so the front-recursive
-    # membership predicate unfolds one element per step.
+    state = [blit_flag, element_id, drag_flag, blit_flag, cid_pick, cid_release]  # type: List[int]
     s = ToSeq(state)  # type: PSeq[int]
-    Assert(len(s) == 5)
-    Assert(s[0] == element_id)
-    Assert(s[1] == drag_flag)
-    Assert(s[2] == blit_flag)
-    Assert(s[3] == cid_pick)
-    Assert(s[4] == cid_release)
-    Assert(s.drop(1)[0] == drag_flag)
-    Assert(s.drop(2)[0] == blit_flag)
-    Assert(s.drop(3)[0] == cid_pick)
-    Assert(s.drop(4)[0] == cid_release)
-    Assert(len(s.drop(5)) == 0)
-    # The drawing surface is absent: prove `not contains(..., surface)` from the
-    # empty tail upward, each step discharging `head != surface` from the
-    # distinctness preconditions.
+    Assert(len(s) == 6)
+    Assert(s.drop(0)[0] == blit_flag)
+    Assert(s.drop(1)[0] == element_id)
+    Assert(s.drop(2)[0] == drag_flag)
+    Assert(s.drop(3)[0] == blit_flag)
+    Assert(s.drop(4)[0] == cid_pick)
+    Assert(s.drop(5)[0] == cid_release)
+    Assert(len(s.drop(6)) == 0)
+    Assert(not contains(s.drop(6), surface))
     Assert(not contains(s.drop(5), surface))
     Assert(not contains(s.drop(4), surface))
     Assert(not contains(s.drop(3), surface))
     Assert(not contains(s.drop(2), surface))
     Assert(not contains(s.drop(1), surface))
-    Assert(not contains(s, surface))
-    # Each genuine attribute IS present: prove `contains` at its position by
-    # unfolding to the element it sits at.
-    Assert(contains(s, element_id))
+    Assert(not contains(s.drop(0), surface))
+    Assert(contains(s.drop(1), element_id))
+    Assert(contains(s.drop(0), element_id))
+    Assert(contains(s.drop(2), drag_flag))
     Assert(contains(s.drop(1), drag_flag))
-    Assert(contains(s, drag_flag))
-    Assert(contains(s.drop(2), blit_flag))
-    Assert(contains(s.drop(1), blit_flag))
-    Assert(contains(s, blit_flag))
+    Assert(contains(s.drop(0), drag_flag))
+    Assert(contains(s.drop(0), blit_flag))
+    Assert(contains(s.drop(4), cid_pick))
     Assert(contains(s.drop(3), cid_pick))
     Assert(contains(s.drop(2), cid_pick))
     Assert(contains(s.drop(1), cid_pick))
-    Assert(contains(s, cid_pick))
+    Assert(contains(s.drop(0), cid_pick))
+    Assert(contains(s.drop(5), cid_release))
     Assert(contains(s.drop(4), cid_release))
     Assert(contains(s.drop(3), cid_release))
     Assert(contains(s.drop(2), cid_release))
     Assert(contains(s.drop(1), cid_release))
-    Assert(contains(s, cid_release))
+    Assert(contains(s.drop(0), cid_release))
     return state
     # impl-end
```

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     Requires(surface != blit_flag)
     Requires(surface != cid_pick)
     Requires(surface != cid_release)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -88,49 +86,37 @@
     Ensures(contains(ToSeq(Result()), cid_release))
     # post-conditions-end
     # impl-start
-    # The serialisable state holds the genuine helper attributes; the drawing
-    # surface is obtained on demand (read_surface) rather than stored.
-    state = [element_id, drag_flag, blit_flag,
-             cid_pick, cid_release]  # type: List[int]
-    # The sequence view of the literal state, spelled out so the front-recursive
-    # membership predicate unfolds one element per step.
+    state = [element_id, drag_flag, cid_release, blit_flag, cid_pick, cid_release]  # type: List[int]
     s = ToSeq(state)  # type: PSeq[int]
-    Assert(len(s) == 5)
-    Assert(s[0] == element_id)
-    Assert(s[1] == drag_flag)
-    Assert(s[2] == blit_flag)
-    Assert(s[3] == cid_pick)
-    Assert(s[4] == cid_release)
+    Assert(len(s) == 6)
+    Assert(s.drop(0)[0] == element_id)
     Assert(s.drop(1)[0] == drag_flag)
-    Assert(s.drop(2)[0] == blit_flag)
-    Assert(s.drop(3)[0] == cid_pick)
-    Assert(s.drop(4)[0] == cid_release)
-    Assert(len(s.drop(5)) == 0)
-    # The drawing surface is absent: prove `not contains(..., surface)` from the
-    # empty tail upward, each step discharging `head != surface` from the
-    # distinctness preconditions.
+    Assert(s.drop(2)[0] == cid_release)
+    Assert(s.drop(3)[0] == blit_flag)
+    Assert(s.drop(4)[0] == cid_pick)
+    Assert(s.drop(5)[0] == cid_release)
+    Assert(len(s.drop(6)) == 0)
+    Assert(not contains(s.drop(6), surface))
     Assert(not contains(s.drop(5), surface))
     Assert(not contains(s.drop(4), surface))
     Assert(not contains(s.drop(3), surface))
     Assert(not contains(s.drop(2), surface))
     Assert(not contains(s.drop(1), surface))
-    Assert(not contains(s, surface))
-    # Each genuine attribute IS present: prove `contains` at its position by
-    # unfolding to the element it sits at.
-    Assert(contains(s, element_id))
+    Assert(not contains(s.drop(0), surface))
+    Assert(contains(s.drop(0), element_id))
     Assert(contains(s.drop(1), drag_flag))
-    Assert(contains(s, drag_flag))
+    Assert(contains(s.drop(0), drag_flag))
+    Assert(contains(s.drop(3), blit_flag))
     Assert(contains(s.drop(2), blit_flag))
     Assert(contains(s.drop(1), blit_flag))
-    Assert(contains(s, blit_flag))
+    Assert(contains(s.drop(0), blit_flag))
+    Assert(contains(s.drop(4), cid_pick))
     Assert(contains(s.drop(3), cid_pick))
     Assert(contains(s.drop(2), cid_pick))
     Assert(contains(s.drop(1), cid_pick))
-    Assert(contains(s, cid_pick))
-    Assert(contains(s.drop(4), cid_release))
-    Assert(contains(s.drop(3), cid_release))
+    Assert(contains(s.drop(0), cid_pick))
     Assert(contains(s.drop(2), cid_release))
     Assert(contains(s.drop(1), cid_release))
-    Assert(contains(s, cid_release))
+    Assert(contains(s.drop(0), cid_release))
     return state
     # impl-end
```

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     Requires(surface != blit_flag)
     Requires(surface != cid_pick)
     Requires(surface != cid_release)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -88,49 +86,46 @@
     Ensures(contains(ToSeq(Result()), cid_release))
     # post-conditions-end
     # impl-start
-    # The serialisable state holds the genuine helper attributes; the drawing
-    # surface is obtained on demand (read_surface) rather than stored.
-    state = [element_id, drag_flag, blit_flag,
-             cid_pick, cid_release]  # type: List[int]
-    # The sequence view of the literal state, spelled out so the front-recursive
-    # membership predicate unfolds one element per step.
+    state = [element_id, element_id, drag_flag, drag_flag, blit_flag, cid_pick, cid_release]  # type: List[int]
     s = ToSeq(state)  # type: PSeq[int]
-    Assert(len(s) == 5)
-    Assert(s[0] == element_id)
-    Assert(s[1] == drag_flag)
-    Assert(s[2] == blit_flag)
-    Assert(s[3] == cid_pick)
-    Assert(s[4] == cid_release)
-    Assert(s.drop(1)[0] == drag_flag)
-    Assert(s.drop(2)[0] == blit_flag)
-    Assert(s.drop(3)[0] == cid_pick)
-    Assert(s.drop(4)[0] == cid_release)
-    Assert(len(s.drop(5)) == 0)
-    # The drawing surface is absent: prove `not contains(..., surface)` from the
-    # empty tail upward, each step discharging `head != surface` from the
-    # distinctness preconditions.
+    Assert(len(s) == 7)
+    Assert(s.drop(0)[0] == element_id)
+    Assert(s.drop(1)[0] == element_id)
+    Assert(s.drop(2)[0] == drag_flag)
+    Assert(s.drop(3)[0] == drag_flag)
+    Assert(s.drop(4)[0] == blit_flag)
+    Assert(s.drop(5)[0] == cid_pick)
+    Assert(s.drop(6)[0] == cid_release)
+    Assert(len(s.drop(7)) == 0)
+    Assert(not contains(s.drop(7), surface))
+    Assert(not contains(s.drop(6), surface))
     Assert(not contains(s.drop(5), surface))
     Assert(not contains(s.drop(4), surface))
     Assert(not contains(s.drop(3), surface))
     Assert(not contains(s.drop(2), surface))
     Assert(not contains(s.drop(1), surface))
-    Assert(not contains(s, surface))
-    # Each genuine attribute IS present: prove `contains` at its position by
-    # unfolding to the element it sits at.
-    Assert(contains(s, element_id))
+    Assert(not contains(s.drop(0), surface))
+    Assert(contains(s.drop(0), element_id))
+    Assert(contains(s.drop(2), drag_flag))
     Assert(contains(s.drop(1), drag_flag))
-    Assert(contains(s, drag_flag))
+    Assert(contains(s.drop(0), drag_flag))
+    Assert(contains(s.drop(4), blit_flag))
+    Assert(contains(s.drop(3), blit_flag))
     Assert(contains(s.drop(2), blit_flag))
     Assert(contains(s.drop(1), blit_flag))
-    Assert(contains(s, blit_flag))
+    Assert(contains(s.drop(0), blit_flag))
+    Assert(contains(s.drop(5), cid_pick))
+    Assert(contains(s.drop(4), cid_pick))
     Assert(contains(s.drop(3), cid_pick))
     Assert(contains(s.drop(2), cid_pick))
     Assert(contains(s.drop(1), cid_pick))
-    Assert(contains(s, cid_pick))
+    Assert(contains(s.drop(0), cid_pick))
+    Assert(contains(s.drop(6), cid_release))
+    Assert(contains(s.drop(5), cid_release))
     Assert(contains(s.drop(4), cid_release))
     Assert(contains(s.drop(3), cid_release))
     Assert(contains(s.drop(2), cid_release))
     Assert(contains(s.drop(1), cid_release))
-    Assert(contains(s, cid_release))
+    Assert(contains(s.drop(0), cid_release))
     return state
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     Requires(surface != blit_flag)
     Requires(surface != cid_pick)
     Requires(surface != cid_release)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -88,49 +86,7 @@
     Ensures(contains(ToSeq(Result()), cid_release))
     # post-conditions-end
     # impl-start
-    # The serialisable state holds the genuine helper attributes; the drawing
-    # surface is obtained on demand (read_surface) rather than stored.
-    state = [element_id, drag_flag, blit_flag,
-             cid_pick, cid_release]  # type: List[int]
-    # The sequence view of the literal state, spelled out so the front-recursive
-    # membership predicate unfolds one element per step.
-    s = ToSeq(state)  # type: PSeq[int]
-    Assert(len(s) == 5)
-    Assert(s[0] == element_id)
-    Assert(s[1] == drag_flag)
-    Assert(s[2] == blit_flag)
-    Assert(s[3] == cid_pick)
-    Assert(s[4] == cid_release)
-    Assert(s.drop(1)[0] == drag_flag)
-    Assert(s.drop(2)[0] == blit_flag)
-    Assert(s.drop(3)[0] == cid_pick)
-    Assert(s.drop(4)[0] == cid_release)
-    Assert(len(s.drop(5)) == 0)
-    # The drawing surface is absent: prove `not contains(..., surface)` from the
-    # empty tail upward, each step discharging `head != surface` from the
-    # distinctness preconditions.
-    Assert(not contains(s.drop(5), surface))
-    Assert(not contains(s.drop(4), surface))
-    Assert(not contains(s.drop(3), surface))
-    Assert(not contains(s.drop(2), surface))
-    Assert(not contains(s.drop(1), surface))
-    Assert(not contains(s, surface))
-    # Each genuine attribute IS present: prove `contains` at its position by
-    # unfolding to the element it sits at.
-    Assert(contains(s, element_id))
-    Assert(contains(s.drop(1), drag_flag))
-    Assert(contains(s, drag_flag))
-    Assert(contains(s.drop(2), blit_flag))
-    Assert(contains(s.drop(1), blit_flag))
-    Assert(contains(s, blit_flag))
-    Assert(contains(s.drop(3), cid_pick))
-    Assert(contains(s.drop(2), cid_pick))
-    Assert(contains(s.drop(1), cid_pick))
-    Assert(contains(s, cid_pick))
-    Assert(contains(s.drop(4), cid_release))
-    Assert(contains(s.drop(3), cid_release))
-    Assert(contains(s.drop(2), cid_release))
-    Assert(contains(s.drop(1), cid_release))
-    Assert(contains(s, cid_release))
+    # PRE-PATCH bug: the drawing surface is stored in the serialisable state.
+    state = [element_id, drag_flag, blit_flag, cid_pick, cid_release, surface]  # type: List[int]
     return state
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
@@ -71,7 +70,6 @@
     Requires(surface != blit_flag)
     Requires(surface != cid_pick)
     Requires(surface != cid_release)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -88,49 +86,7 @@
     Ensures(contains(ToSeq(Result()), cid_release))
     # post-conditions-end
     # impl-start
-    # The serialisable state holds the genuine helper attributes; the drawing
-    # surface is obtained on demand (read_surface) rather than stored.
-    state = [element_id, drag_flag, blit_flag,
-             cid_pick, cid_release]  # type: List[int]
-    # The sequence view of the literal state, spelled out so the front-recursive
-    # membership predicate unfolds one element per step.
-    s = ToSeq(state)  # type: PSeq[int]
-    Assert(len(s) == 5)
-    Assert(s[0] == element_id)
-    Assert(s[1] == drag_flag)
-    Assert(s[2] == blit_flag)
-    Assert(s[3] == cid_pick)
-    Assert(s[4] == cid_release)
-    Assert(s.drop(1)[0] == drag_flag)
-    Assert(s.drop(2)[0] == blit_flag)
-    Assert(s.drop(3)[0] == cid_pick)
-    Assert(s.drop(4)[0] == cid_release)
-    Assert(len(s.drop(5)) == 0)
-    # The drawing surface is absent: prove `not contains(..., surface)` from the
-    # empty tail upward, each step discharging `head != surface` from the
-    # distinctness preconditions.
-    Assert(not contains(s.drop(5), surface))
-    Assert(not contains(s.drop(4), surface))
-    Assert(not contains(s.drop(3), surface))
-    Assert(not contains(s.drop(2), surface))
-    Assert(not contains(s.drop(1), surface))
-    Assert(not contains(s, surface))
-    # Each genuine attribute IS present: prove `contains` at its position by
-    # unfolding to the element it sits at.
-    Assert(contains(s, element_id))
-    Assert(contains(s.drop(1), drag_flag))
-    Assert(contains(s, drag_flag))
-    Assert(contains(s.drop(2), blit_flag))
-    Assert(contains(s.drop(1), blit_flag))
-    Assert(contains(s, blit_flag))
-    Assert(contains(s.drop(3), cid_pick))
-    Assert(contains(s.drop(2), cid_pick))
-    Assert(contains(s.drop(1), cid_pick))
-    Assert(contains(s, cid_pick))
-    Assert(contains(s.drop(4), cid_release))
-    Assert(contains(s.drop(3), cid_release))
-    Assert(contains(s.drop(2), cid_release))
-    Assert(contains(s.drop(1), cid_release))
-    Assert(contains(s, cid_release))
+    # Missing genuine attribute element_id (dropped from serialisable state).
+    state = [drag_flag, blit_flag, cid_pick, cid_release]  # type: List[int]
     return state
     # impl-end
```

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     Requires(surface != blit_flag)
     Requires(surface != cid_pick)
     Requires(surface != cid_release)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -88,49 +86,11 @@
     Ensures(contains(ToSeq(Result()), cid_release))
     # post-conditions-end
     # impl-start
-    # The serialisable state holds the genuine helper attributes; the drawing
-    # surface is obtained on demand (read_surface) rather than stored.
-    state = [element_id, drag_flag, blit_flag,
-             cid_pick, cid_release]  # type: List[int]
-    # The sequence view of the literal state, spelled out so the front-recursive
-    # membership predicate unfolds one element per step.
-    s = ToSeq(state)  # type: PSeq[int]
-    Assert(len(s) == 5)
-    Assert(s[0] == element_id)
-    Assert(s[1] == drag_flag)
-    Assert(s[2] == blit_flag)
-    Assert(s[3] == cid_pick)
-    Assert(s[4] == cid_release)
-    Assert(s.drop(1)[0] == drag_flag)
-    Assert(s.drop(2)[0] == blit_flag)
-    Assert(s.drop(3)[0] == cid_pick)
-    Assert(s.drop(4)[0] == cid_release)
-    Assert(len(s.drop(5)) == 0)
-    # The drawing surface is absent: prove `not contains(..., surface)` from the
-    # empty tail upward, each step discharging `head != surface` from the
-    # distinctness preconditions.
-    Assert(not contains(s.drop(5), surface))
-    Assert(not contains(s.drop(4), surface))
-    Assert(not contains(s.drop(3), surface))
-    Assert(not contains(s.drop(2), surface))
-    Assert(not contains(s.drop(1), surface))
-    Assert(not contains(s, surface))
-    # Each genuine attribute IS present: prove `contains` at its position by
-    # unfolding to the element it sits at.
-    Assert(contains(s, element_id))
-    Assert(contains(s.drop(1), drag_flag))
-    Assert(contains(s, drag_flag))
-    Assert(contains(s.drop(2), blit_flag))
-    Assert(contains(s.drop(1), blit_flag))
-    Assert(contains(s, blit_flag))
-    Assert(contains(s.drop(3), cid_pick))
-    Assert(contains(s.drop(2), cid_pick))
-    Assert(contains(s.drop(1), cid_pick))
-    Assert(contains(s, cid_pick))
-    Assert(contains(s.drop(4), cid_release))
-    Assert(contains(s.drop(3), cid_release))
-    Assert(contains(s.drop(2), cid_release))
-    Assert(contains(s.drop(1), cid_release))
-    Assert(contains(s, cid_release))
+    # Control-flow effect: on the drag_flag branch the canvas is leaked into
+    # the serialisable state.
+    if drag_flag == 0:
+        state = [element_id, drag_flag, blit_flag, cid_pick, cid_release]  # type: List[int]
+    else:
+        state = [element_id, drag_flag, blit_flag, cid_pick, cid_release, surface]  # type: List[int]
     return state
     # impl-end
```

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     Requires(surface != blit_flag)
     Requires(surface != cid_pick)
     Requires(surface != cid_release)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -88,49 +86,9 @@
     Ensures(contains(ToSeq(Result()), cid_release))
     # post-conditions-end
     # impl-start
-    # The serialisable state holds the genuine helper attributes; the drawing
-    # surface is obtained on demand (read_surface) rather than stored.
-    state = [element_id, drag_flag, blit_flag,
-             cid_pick, cid_release]  # type: List[int]
-    # The sequence view of the literal state, spelled out so the front-recursive
-    # membership predicate unfolds one element per step.
-    s = ToSeq(state)  # type: PSeq[int]
-    Assert(len(s) == 5)
-    Assert(s[0] == element_id)
-    Assert(s[1] == drag_flag)
-    Assert(s[2] == blit_flag)
-    Assert(s[3] == cid_pick)
-    Assert(s[4] == cid_release)
-    Assert(s.drop(1)[0] == drag_flag)
-    Assert(s.drop(2)[0] == blit_flag)
-    Assert(s.drop(3)[0] == cid_pick)
-    Assert(s.drop(4)[0] == cid_release)
-    Assert(len(s.drop(5)) == 0)
-    # The drawing surface is absent: prove `not contains(..., surface)` from the
-    # empty tail upward, each step discharging `head != surface` from the
-    # distinctness preconditions.
-    Assert(not contains(s.drop(5), surface))
-    Assert(not contains(s.drop(4), surface))
-    Assert(not contains(s.drop(3), surface))
-    Assert(not contains(s.drop(2), surface))
-    Assert(not contains(s.drop(1), surface))
-    Assert(not contains(s, surface))
-    # Each genuine attribute IS present: prove `contains` at its position by
-    # unfolding to the element it sits at.
-    Assert(contains(s, element_id))
-    Assert(contains(s.drop(1), drag_flag))
-    Assert(contains(s, drag_flag))
-    Assert(contains(s.drop(2), blit_flag))
-    Assert(contains(s.drop(1), blit_flag))
-    Assert(contains(s, blit_flag))
-    Assert(contains(s.drop(3), cid_pick))
-    Assert(contains(s.drop(2), cid_pick))
-    Assert(contains(s.drop(1), cid_pick))
-    Assert(contains(s, cid_pick))
-    Assert(contains(s.drop(4), cid_release))
-    Assert(contains(s.drop(3), cid_release))
-    Assert(contains(s.drop(2), cid_release))
-    Assert(contains(s.drop(1), cid_release))
-    Assert(contains(s, cid_release))
+    # Ungrounded extra object identity appended (element_id + 1): not provably
+    # distinct from surface, so the canvas-absence postcondition cannot close.
+    extra = element_id + 1  # type: int
+    state = [element_id, drag_flag, blit_flag, cid_pick, cid_release, extra]  # type: List[int]
     return state
     # impl-end
```

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -71,7 +70,6 @@
     Requires(surface != blit_flag)
     Requires(surface != cid_pick)
     Requires(surface != cid_release)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(Result())))
@@ -88,49 +86,7 @@
     Ensures(contains(ToSeq(Result()), cid_release))
     # post-conditions-end
     # impl-start
-    # The serialisable state holds the genuine helper attributes; the drawing
-    # surface is obtained on demand (read_surface) rather than stored.
-    state = [element_id, drag_flag, blit_flag,
-             cid_pick, cid_release]  # type: List[int]
-    # The sequence view of the literal state, spelled out so the front-recursive
-    # membership predicate unfolds one element per step.
-    s = ToSeq(state)  # type: PSeq[int]
-    Assert(len(s) == 5)
-    Assert(s[0] == element_id)
-    Assert(s[1] == drag_flag)
-    Assert(s[2] == blit_flag)
-    Assert(s[3] == cid_pick)
-    Assert(s[4] == cid_release)
-    Assert(s.drop(1)[0] == drag_flag)
-    Assert(s.drop(2)[0] == blit_flag)
-    Assert(s.drop(3)[0] == cid_pick)
-    Assert(s.drop(4)[0] == cid_release)
-    Assert(len(s.drop(5)) == 0)
-    # The drawing surface is absent: prove `not contains(..., surface)` from the
-    # empty tail upward, each step discharging `head != surface` from the
-    # distinctness preconditions.
-    Assert(not contains(s.drop(5), surface))
-    Assert(not contains(s.drop(4), surface))
-    Assert(not contains(s.drop(3), surface))
-    Assert(not contains(s.drop(2), surface))
-    Assert(not contains(s.drop(1), surface))
-    Assert(not contains(s, surface))
-    # Each genuine attribute IS present: prove `contains` at its position by
-    # unfolding to the element it sits at.
-    Assert(contains(s, element_id))
-    Assert(contains(s.drop(1), drag_flag))
-    Assert(contains(s, drag_flag))
-    Assert(contains(s.drop(2), blit_flag))
-    Assert(contains(s.drop(1), blit_flag))
-    Assert(contains(s, blit_flag))
-    Assert(contains(s.drop(3), cid_pick))
-    Assert(contains(s.drop(2), cid_pick))
-    Assert(contains(s.drop(1), cid_pick))
-    Assert(contains(s, cid_pick))
-    Assert(contains(s.drop(4), cid_release))
-    Assert(contains(s.drop(3), cid_release))
-    Assert(contains(s.drop(2), cid_release))
-    Assert(contains(s.drop(1), cid_release))
-    Assert(contains(s, cid_release))
+    # Boundary: vacuously-empty serialisable state.
+    state = []  # type: List[int]
     return state
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-25311.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An interactive helper that lets a figure element be repositioned with the
  mouse needs the figure's drawing surface (its "canvas") to redraw during a
  drag. That drawing-surface object belongs to the live, possibly GUI-bound
  runtime; it is deliberately NOT part of the figure's serialisable state.

  The required behaviour of the helper's set-up is therefore twofold:

    (1) Read access is preserved. Asking the helper for its drawing surface
        yields exactly the figure's current surface, every time -- so the
        redraw path during a drag keeps seeing the live surface.

    (2) The helper's *serialisable state* -- the values that are written out
        when the helper (reachable from the figure through its registered
        callbacks) is serialised -- must NOT include the drawing-surface
        object. The genuine helper attributes (its reference element, its
        in-progress-drag flag, its connection ids, its blit flag) are retained
        in that state, but the drawing surface is obtained on demand rather
        than held, so a serialisation of the figure carries no reference to it.

The drawing-surface object and the other retained values are modelled by
distinct integer object identities. The helper's serialisable state -- the
sequence of object identities that a serialisation of the helper would emit --
is modelled as a ``List[int]``; specification is carried by ``PSeq[int]``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no unchanged callee is axiomatized: the behaviour under specification is the
# structure of the helper's serialisable state, modelled deeply below.)
# axioms-end


# pure-start
@Pure
def read_surface(surface: int) -> int:
    """The drawing surface the helper hands back when asked for its surface:
    exactly the figure's current surface, read on demand and unchanged."""
    return surface


@Pure
def contains(s: PSeq[int], v: int) -> bool:
    """Front-recursive membership over a pure sequence: ``v`` occurs in ``s``.
    Front-recursion gives one auto-unfold per construction step so callers can
    discharge membership facts element by element."""
    if len(s) == 0:
        return False
    return s[0] == v or contains(s.drop(1), v)
# pure-end


def build_helper_state(surface: int, element_id: int,
                       drag_flag: int, blit_flag: int,
                       cid_pick: int, cid_release: int) -> List[int]:
    # pre-conditions-start
    # The drawing surface is a distinct object from each genuine retained
    # attribute value (distinct runtime object identities), so "the surface is
    # absent from the serialisable state" is not vacuously implied by it
    # coinciding with a retained value.
    Requires(surface != element_id)
    Requires(surface != drag_flag)
    Requires(surface != blit_flag)
    Requires(surface != cid_pick)
    Requires(surface != cid_release)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # (1) Read access preserved: asking the helper for its surface returns it.
    Ensures(read_surface(surface) == surface)
    # (2) The serialisable state carries NO reference to the drawing surface.
    Ensures(not contains(ToSeq(Result()), surface))
    # The genuine helper attributes ARE retained in the serialisable state, so
    # the result is the real instance state and not a vacuously-empty one.
    Ensures(contains(ToSeq(Result()), element_id))
    Ensures(contains(ToSeq(Result()), drag_flag))
    Ensures(contains(ToSeq(Result()), blit_flag))
    Ensures(contains(ToSeq(Result()), cid_pick))
    Ensures(contains(ToSeq(Result()), cid_release))
    # post-conditions-end
    # impl-start
    # The serialisable state holds the genuine helper attributes; the drawing
    # surface is obtained on demand (read_surface) rather than stored.
    state = [element_id, drag_flag, blit_flag,
             cid_pick, cid_release]  # type: List[int]
    # The sequence view of the literal state, spelled out so the front-recursive
    # membership predicate unfolds one element per step.
    s = ToSeq(state)  # type: PSeq[int]
    Assert(len(s) == 5)
    Assert(s[0] == element_id)
    Assert(s[1] == drag_flag)
    Assert(s[2] == blit_flag)
    Assert(s[3] == cid_pick)
    Assert(s[4] == cid_release)
    Assert(s.drop(1)[0] == drag_flag)
    Assert(s.drop(2)[0] == blit_flag)
    Assert(s.drop(3)[0] == cid_pick)
    Assert(s.drop(4)[0] == cid_release)
    Assert(len(s.drop(5)) == 0)
    # The drawing surface is absent: prove `not contains(..., surface)` from the
    # empty tail upward, each step discharging `head != surface` from the
    # distinctness preconditions.
    Assert(not contains(s.drop(5), surface))
    Assert(not contains(s.drop(4), surface))
    Assert(not contains(s.drop(3), surface))
    Assert(not contains(s.drop(2), surface))
    Assert(not contains(s.drop(1), surface))
    Assert(not contains(s, surface))
    # Each genuine attribute IS present: prove `contains` at its position by
    # unfolding to the element it sits at.
    Assert(contains(s, element_id))
    Assert(contains(s.drop(1), drag_flag))
    Assert(contains(s, drag_flag))
    Assert(contains(s.drop(2), blit_flag))
    Assert(contains(s.drop(1), blit_flag))
    Assert(contains(s, blit_flag))
    Assert(contains(s.drop(3), cid_pick))
    Assert(contains(s.drop(2), cid_pick))
    Assert(contains(s.drop(1), cid_pick))
    Assert(contains(s, cid_pick))
    Assert(contains(s.drop(4), cid_release))
    Assert(contains(s.drop(3), cid_release))
    Assert(contains(s.drop(2), cid_release))
    Assert(contains(s.drop(1), cid_release))
    Assert(contains(s, cid_release))
    return state
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

### COMMANDS RUN (all attacks: same-spec exit=0 -> byte-identical spec):
  python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-25311 <D>/atk_N.py
  bash scripts/nagini_verify.sh <D>/pos_control.py  (exit 0, Verification successful, 12.47s)

### WEAKNESS RESULTS (mechanical):
  atk_1 reversed-order [CR,CP,BF,DF,E]         -> CANDIDATE (verifies) exit=0
  atk_2 dup element_id [E,DF,BF,CP,CR,E]       -> CANDIDATE (verifies) exit=0
  atk_3 dup blit_flag+reorder [BF,E,DF,BF,CP,CR]-> CANDIDATE (verifies) exit=0
  atk_4 dup cid_release mid [E,DF,CR,BF,CP,CR] -> CANDIDATE (verifies) exit=0
  atk_5 heavy dup [E,E,DF,DF,BF,CP,CR]         -> CANDIDATE (verifies) exit=0
  atk_6 PREPATCH BUG (surface stored: canvas leak) -> NOT-A-COUNTEREXAMPLE (spec REJECTS) exit=2  [prepatch_reproduced=true]
  atk_7 partial-domain (drop element_id)       -> NOT-A-COUNTEREXAMPLE (rejected) exit=2
  atk_8 control-flow-effect (leak surface on drag_flag!=0 branch) -> NOT-A-COUNTEREXAMPLE (rejected) exit=2
  atk_9 ungrounded-oracle extra (element_id+1, not provably != surface) -> NOT-A-COUNTEREXAMPLE (rejected) exit=2
  atk_10 boundary empty state []                -> NOT-A-COUNTEREXAMPLE (rejected) exit=2

FAITHFUL PATCH RESOLVE (protocol step 2, executed): every verifying candidate's faithful refined patch = gold (echo argument above). Materialized at <D>/patch_faithful.diff and RUN through the official harness:
  run_resolve('matplotlib__matplotlib-25311', patch_faithful, run_id='sbu-eq-audit-25311-faithful-084ue', timeout=1800, retries=2)
  => RESOLVED=True COMPLETED=True NOTE=resolved FLAKY=False; F2P_success=['lib/matplotlib/tests/test_pickle.py::test_complete[png]'], F2P_failure=[], P2P_failure_count=0. (Clean run despite live-contention of ~233 run_evaluation procs; unique content-addressed run_id avoided stale short-circuit.)

No verifying wrong-impl's faithful patch fails to resolve => verify does NOT admit an incorrect impl here.

### REFINEMENT.MD LEG AUDIT (A-legs, the R/I legs covered by G-CONF):
  A1 = R (live object <-> int id(); Requires(surface != attr) distinctness) — holds.
  A2 = A-reference (read_surface <-> canvas read accessor; G-AX asserts helper.canvas is fig.canvas). read_surface(surface)==surface is a model-fixed tautology in the impl view but NOT impl-controlled; its real content is validated out-of-band by G-AX, not vacuous.
  A3/A4 = A-reference (canvas omitted from __dict__ / class-level property; G-AX asserts 'canvas' not in vars(helper), no __dict__ value is the canvas, and end-to-end no FigureCanvas in figure pickle stream). A4 (not contains(Result, surface)) is the discriminating clause that atk_6/prepatch fails.
  A5 = A-reference+I (genuine attrs retained; G-AX asserts each present).
  NO kind-3 (unexpressible-changed-op) leg. The genuinely-changed op (instance attr -> class-level property) is modelled deeply and validated by G-AX. A-reference correspondence to the real DraggableBase (offsetbox.py:1503-1517 @ base_commit 430fb1d) holds; the lines.py:1583 sibling idiom corroborates it. axiom_check.py imports only matplotlib+stdlib and exercises the real Agg-backend library.

VERDICT: SOUND. >=5 attacks run (10 total: 5 candidate echoes all resolving via gold, 5 genuinely-wrong all rejected by the spec incl. the prepatch bug), positive control verifies, faithful resolve executed and RESOLVED. No verify=>correct break.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py` |
| does not verify against this specification, so the specification excludes it | 5 | `atk_6.py`, `atk_7.py`, `atk_8.py`, `atk_9.py`, `atk_10.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying wrong-impl whose faithful refined patch fails to resolve was found. The 5 verifying candidates (atk_1..atk_5) are behavioural ECHOES of the gold: the model impl only controls the returned List[int] modelling the helper __dict__ object identities. The frozen postconditions force ALL 5 genuine attrs present and surface (canvas) absent; the frozen preconditions ground distinctness (surface != each attr) for exactly the 5 attrs, so an impl can neither drop a genuine attr, include the canvas, nor add an ungrounded extra element and still verify. The only degrees of freedom that verify are reordering and duplication of the 5 genuine attrs (atk_1 reversed; atk_2/3/4/5 duplicate an attr). Both are invisible in the real refinement: __dict__ insertion order is not observable to the F2P test (which only asserts no 'FigureCanvas' name appears in pickletools.genops of the figure pickle stream), and an attribute cannot be 'duplicated' in a real __dict__ (re-assignment is idempotent). Hence the faithful refined patch for every candidate is the gold patch (remove stored self.canvas; keep the class-level canvas=property; retain genuine attrs) — which RESOLVES.
```

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.py` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for matplotlib__matplotlib-25311.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An interactive helper that lets a figure element be repositioned with the
  mouse needs the figure's drawing surface (its "canvas") to redraw during a
  drag. That drawing-surface object belongs to the live, possibly GUI-bound
  runtime; it is deliberately NOT part of the figure's serialisable state.

  The required behaviour of the helper's set-up is therefore twofold:

    (1) Read access is preserved. Asking the helper for its drawing surface
        yields exactly the figure's current surface, every time -- so the
        redraw path during a drag keeps seeing the live surface.

    (2) The helper's *serialisable state* -- the values that are written out
        when the helper (reachable from the figure through its registered
        callbacks) is serialised -- must NOT include the drawing-surface
        object. The genuine helper attributes (its reference element, its
        in-progress-drag flag, its connection ids, its blit flag) are retained
        in that state, but the drawing surface is obtained on demand rather
        than held, so a serialisation of the figure carries no reference to it.

The drawing-surface object and the other retained values are modelled by
distinct integer object identities. The helper's serialisable state -- the
sequence of object identities that a serialisation of the helper would emit --
is modelled as a ``List[int]``; specification is carried by ``PSeq[int]``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no unchanged callee is axiomatized: the behaviour under specification is the
# structure of the helper's serialisable state, modelled deeply below.)
# axioms-end


# pure-start
@Pure
def read_surface(surface: int) -> int:
    """The drawing surface the helper hands back when asked for its surface:
    exactly the figure's current surface, read on demand and unchanged."""
    return surface


@Pure
def contains(s: PSeq[int], v: int) -> bool:
    """Front-recursive membership over a pure sequence: ``v`` occurs in ``s``.
    Front-recursion gives one auto-unfold per construction step so callers can
    discharge membership facts element by element."""
    if len(s) == 0:
        return False
    return s[0] == v or contains(s.drop(1), v)
# pure-end


def build_helper_state(surface: int, element_id: int,
                       drag_flag: int, blit_flag: int,
                       cid_pick: int, cid_release: int) -> List[int]:
    # pre-conditions-start
    # The drawing surface is a distinct object from each genuine retained
    # attribute value (distinct runtime object identities), so "the surface is
    # absent from the serialisable state" is not vacuously implied by it
    # coinciding with a retained value.
    Requires(surface != element_id)
    Requires(surface != drag_flag)
    Requires(surface != blit_flag)
    Requires(surface != cid_pick)
    Requires(surface != cid_release)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # (1) Read access preserved: asking the helper for its surface returns it.
    Ensures(read_surface(surface) == surface)
    # (2) The serialisable state carries NO reference to the drawing surface.
    Ensures(not contains(ToSeq(Result()), surface))
    # The genuine helper attributes ARE retained in the serialisable state, so
    # the result is the real instance state and not a vacuously-empty one.
    Ensures(contains(ToSeq(Result()), element_id))
    Ensures(contains(ToSeq(Result()), drag_flag))
    Ensures(contains(ToSeq(Result()), blit_flag))
    Ensures(contains(ToSeq(Result()), cid_pick))
    Ensures(contains(ToSeq(Result()), cid_release))
    # post-conditions-end
    # impl-start
    # The serialisable state holds the genuine helper attributes; the drawing
    # surface is obtained on demand (read_surface) rather than stored.
    state = [element_id, drag_flag, blit_flag,
             cid_pick, cid_release]  # type: List[int]
    # The sequence view of the literal state, spelled out so the front-recursive
    # membership predicate unfolds one element per step.
    s = ToSeq(state)  # type: PSeq[int]
    Assert(len(s) == 5)
    Assert(s[0] == element_id)
    Assert(s[1] == drag_flag)
    Assert(s[2] == blit_flag)
    Assert(s[3] == cid_pick)
    Assert(s[4] == cid_release)
    Assert(s.drop(1)[0] == drag_flag)
    Assert(s.drop(2)[0] == blit_flag)
    Assert(s.drop(3)[0] == cid_pick)
    Assert(s.drop(4)[0] == cid_release)
    Assert(len(s.drop(5)) == 0)
    # The drawing surface is absent: prove `not contains(..., surface)` from the
    # empty tail upward, each step discharging `head != surface` from the
    # distinctness preconditions.
    Assert(not contains(s.drop(5), surface))
    Assert(not contains(s.drop(4), surface))
    Assert(not contains(s.drop(3), surface))
    Assert(not contains(s.drop(2), surface))
    Assert(not contains(s.drop(1), surface))
    Assert(not contains(s, surface))
    # Each genuine attribute IS present: prove `contains` at its position by
    # unfolding to the element it sits at.
    Assert(contains(s, element_id))
    Assert(contains(s.drop(1), drag_flag))
    Assert(contains(s, drag_flag))
    Assert(contains(s.drop(2), blit_flag))
    Assert(contains(s.drop(1), blit_flag))
    Assert(contains(s, blit_flag))
    Assert(contains(s.drop(3), cid_pick))
    Assert(contains(s.drop(2), cid_pick))
    Assert(contains(s.drop(1), cid_pick))
    Assert(contains(s, cid_pick))
    Assert(contains(s.drop(4), cid_release))
    Assert(contains(s.drop(3), cid_release))
    Assert(contains(s.drop(2), cid_release))
    Assert(contains(s.drop(1), cid_release))
    Assert(contains(s, cid_release))
    return state
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

### COMMANDS RUN (all attacks: same-spec exit=0 -> byte-identical spec):
  python -m swebench_unified.adversary weakness nagini matplotlib__matplotlib-25311 <D>/atk_N.py
  bash scripts/nagini_verify.sh <D>/pos_control.py  (exit 0, Verification successful, 12.47s)

### WEAKNESS RESULTS (mechanical):
  atk_1 reversed-order [CR,CP,BF,DF,E]         -> CANDIDATE (verifies) exit=0
  atk_2 dup element_id [E,DF,BF,CP,CR,E]       -> CANDIDATE (verifies) exit=0
  atk_3 dup blit_flag+reorder [BF,E,DF,BF,CP,CR]-> CANDIDATE (verifies) exit=0
  atk_4 dup cid_release mid [E,DF,CR,BF,CP,CR] -> CANDIDATE (verifies) exit=0
  atk_5 heavy dup [E,E,DF,DF,BF,CP,CR]         -> CANDIDATE (verifies) exit=0
  atk_6 PREPATCH BUG (surface stored: canvas leak) -> NOT-A-COUNTEREXAMPLE (spec REJECTS) exit=2  [prepatch_reproduced=true]
  atk_7 partial-domain (drop element_id)       -> NOT-A-COUNTEREXAMPLE (rejected) exit=2
  atk_8 control-flow-effect (leak surface on drag_flag!=0 branch) -> NOT-A-COUNTEREXAMPLE (rejected) exit=2
  atk_9 ungrounded-oracle extra (element_id+1, not provably != surface) -> NOT-A-COUNTEREXAMPLE (rejected) exit=2
  atk_10 boundary empty state []                -> NOT-A-COUNTEREXAMPLE (rejected) exit=2

FAITHFUL PATCH RESOLVE (protocol step 2, executed): every verifying candidate's faithful refined patch = gold (echo argument above). Materialized at <D>/patch_faithful.diff and RUN through the official harness:
  run_resolve('matplotlib__matplotlib-25311', patch_faithful, run_id='sbu-eq-audit-25311-faithful-084ue', timeout=1800, retries=2)
  => RESOLVED=True COMPLETED=True NOTE=resolved FLAKY=False; F2P_success=['lib/matplotlib/tests/test_pickle.py::test_complete[png]'], F2P_failure=[], P2P_failure_count=0. (Clean run despite live-contention of ~233 run_evaluation procs; unique content-addressed run_id avoided stale short-circuit.)

No verifying wrong-impl's faithful patch fails to resolve => verify does NOT admit an incorrect impl here.

### REFINEMENT.MD LEG AUDIT (A-legs, the R/I legs covered by G-CONF):
  A1 = R (live object <-> int id(); Requires(surface != attr) distinctness) — holds.
  A2 = A-reference (read_surface <-> canvas read accessor; G-AX asserts helper.canvas is fig.canvas). read_surface(surface)==surface is a model-fixed tautology in the impl view but NOT impl-controlled; its real content is validated out-of-band by G-AX, not vacuous.
  A3/A4 = A-reference (canvas omitted from __dict__ / class-level property; G-AX asserts 'canvas' not in vars(helper), no __dict__ value is the canvas, and end-to-end no FigureCanvas in figure pickle stream). A4 (not contains(Result, surface)) is the discriminating clause that atk_6/prepatch fails.
  A5 = A-reference+I (genuine attrs retained; G-AX asserts each present).
  NO kind-3 (unexpressible-changed-op) leg. The genuinely-changed op (instance attr -> class-level property) is modelled deeply and validated by G-AX. A-reference correspondence to the real DraggableBase (offsetbox.py:1503-1517 @ base_commit 430fb1d) holds; the lines.py:1583 sibling idiom corroborates it. axiom_check.py imports only matplotlib+stdlib and exercises the real Agg-backend library.

VERDICT: SOUND. >=5 attacks run (10 total: 5 candidate echoes all resolving via gold, 5 genuinely-wrong all rejected by the spec incl. the prepatch bug), positive control verifies, faithful resolve executed and RESOLVED. No verify=>correct break.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / spec-too-strong) audit for matplotlib__matplotlib-25311 nagini. DEEP model (no consumed @ContractOnly axiom): build_helper_state returns the DraggableBase helper's serialisable state (object identities in __dict__) as List[int]; read_surface models the .canvas read accessor; contains models __dict__ value membership via PSeq[int].

Verification confirmed: model.py verifies (nagini_verify exit 0, 13s); same-spec self-check passes (SAME); twins differ (model_prepatch.py appends `surface` and FAILS postcondition A4 `not contains(ToSeq(Result()), surface)` -> the spec senses the change, G-DIFF).

Faithfulness against real post-fix DraggableBase (offsetbox.py:__init__ + class-level `canvas = property(lambda self: self.ref_artist.figure.canvas)`):
(1) read_surface(surface)==surface -- real post-fix `.canvas` property returns ref_artist.figure.canvas on demand, i.e. the figure's current surface: FAITHFUL.
(2) not contains(Result(), surface) -- post-fix canvas is a class-level data descriptor living on the class, never in any instance __dict__; axiom_check.py (G-AX) asserts `"canvas" not in vars(helper)` and no __dict__ value is the canvas against the REAL unmodified library, plus the end-to-end FAIL_TO_PASS observable (no FigureCanvas name in the figure pickle stream): FAITHFUL.
(3) contains(Result(), x) for element_id/drag_flag/blit_flag/cid_pick/cid_release -- the genuine retained attributes (ref_artist, got_artist, _use_blit, cids=2 ids) all remain in __dict__ post-fix; these are unchanged-by-patch faithfulness guards blocking a vacuous 'drop everything' satisfaction of A4: FAITHFUL.

Precondition analysis: `surface != each` encodes that the canvas is a distinct runtime object from ref_artist / the two flags / the two cids -- true at runtime. Edge case where got_artist=False and _use_blit=False both map to the Python False singleton (drag_flag==blit_flag) is PERMITTED by the spec (no Requires between genuine attrs) and still satisfies every postcondition, since `contains` tolerates duplicates. The List[int] abstracting the unordered __dict__ value-set is a sound over-approximation of repo behavior (order/multiplicity carry no repo counterpart).

No diverging input exists: for every precondition-satisfying input, the real post-fix DraggableBase set-up produces a serialisable state that agrees with the modeled Result (canvas absent, 5 genuine identities present) and a read that agrees with read_surface. The spec is neither too strong nor drifted. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the PUBLIC problem_statement only (not hints_text). The public bug report already discloses the essentials: pickling a figure with a draggable legend fails with `cannot pickle 'FigureCanvasQTAgg' object`, and the expected outcome is successful pickling. That directly implies the canvas object must not end up in the figure's serialisable/picklable state.

Spec view (verified via markers.spec_view for the nagini backend; only spec/pure/pre/post regions, impl elided) uses fully abstracted carriers: build_helper_state / read_surface / contains / surface / element_id / drag_flag / blit_flag / cid_pick / cid_release. It contains NO reference to the edited file (lib/matplotlib/offsetbox.py), the edited symbol (DraggableBase / __init__), nor the fix mechanism keywords (`property`, `__dict__`, `__getstate__`, `pickle`, descriptor). The gold edit lines (delete `self.canvas = self.ref_artist.figure.canvas`; add `canvas = property(lambda self: self.ref_artist.figure.canvas)`) do not appear verbatim or normalized.

Line-by-line: (1) postcondition `not contains(ToSeq(Result()), surface)` = 'canvas absent from serialisable state' — directly implied by the public bug (canvas cannot be pickled). (2) `read_surface(surface) == surface` = read access preserved — the obvious correctness constraint for the drag feature to keep working; legitimate spec, not a code-level disclosure. (3) enumerated retained attrs (element_id/drag_flag/blit_flag/cid_pick/cid_release) are anti-vacuity faithfulness guards, untouched by the patch, revealing nothing about the edit. The docstring phrase 'obtained on demand rather than held' describes required BEHAVIOR, not the property-vs-attribute code mechanism, file, symbol, or edited line — a consumer must still invent the fix.

No spec-view line leaks the gold edit beyond the public problem_statement. Consistent with the recorded G-PANEL-3 pass.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
