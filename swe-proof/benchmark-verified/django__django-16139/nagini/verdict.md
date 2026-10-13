# P2 adversarial audit — django__django-16139

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk5.py`, `atk6.py`, `atk7.py`, `atk8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk9.py`, `atk10.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
                                             prefix[k] >= 0), [[prefix[k]]])))
     Requires(token >= 0 and current_action >= 0 and pk >= 0
              and secondary_action >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -104,37 +102,6 @@
     )
     # post-conditions-end
     # impl-start
-    # rel = ['..', '..', <pk>, <secondary_action>]
-    result = [DOTDOT(), DOTDOT(), pk, secondary_action]  # type: List[int]
-    # --- proof that resolving rel against the current location yields the
-    #     pk-keyed target (one unfold of `resolve` per step). ---
-    base0 = ToSeq(prefix) + PSeq(token) + PSeq(current_action)
-    rel = ToSeq(result)
-    # rel = [DOTDOT, DOTDOT, pk, secondary_action]
-    Assert(len(rel) == 4)
-    Assert(rel[0] == DOTDOT())
-    Assert(rel.drop(1)[0] == DOTDOT())
-    Assert(rel.drop(1).drop(1)[0] == pk)
-    Assert(rel.drop(1).drop(1).drop(1)[0] == secondary_action)
-    # base sequences after each pop / push, with the take/drop algebra facts.
-    base1 = ToSeq(prefix) + PSeq(token)
-    Assert(base0.take(len(base0) - 1) == base1)
-    Assert(base1.take(len(base1) - 1) == ToSeq(prefix))
-    # pk and secondary_action are ordinary (>= 0) segments, not DOTDOT (-1).
-    Assert(pk != DOTDOT())
-    Assert(secondary_action != DOTDOT())
-    # Unfold `resolve` one rel-step at a time (front-recursion), from the empty
-    # tail backwards, so each equality is a single definitional unfold.
-    Assert(resolve(ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action),
-                   rel.drop(1).drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix) + PSeq(pk), rel.drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix), rel.drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base1, rel.drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base0, rel)
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
+    result = [DOTDOT(), secondary_action]  # type: List[int]
     return result
     # impl-end
```

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
                                             prefix[k] >= 0), [[prefix[k]]])))
     Requires(token >= 0 and current_action >= 0 and pk >= 0
              and secondary_action >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -104,37 +102,6 @@
     )
     # post-conditions-end
     # impl-start
-    # rel = ['..', '..', <pk>, <secondary_action>]
-    result = [DOTDOT(), DOTDOT(), pk, secondary_action]  # type: List[int]
-    # --- proof that resolving rel against the current location yields the
-    #     pk-keyed target (one unfold of `resolve` per step). ---
-    base0 = ToSeq(prefix) + PSeq(token) + PSeq(current_action)
-    rel = ToSeq(result)
-    # rel = [DOTDOT, DOTDOT, pk, secondary_action]
-    Assert(len(rel) == 4)
-    Assert(rel[0] == DOTDOT())
-    Assert(rel.drop(1)[0] == DOTDOT())
-    Assert(rel.drop(1).drop(1)[0] == pk)
-    Assert(rel.drop(1).drop(1).drop(1)[0] == secondary_action)
-    # base sequences after each pop / push, with the take/drop algebra facts.
-    base1 = ToSeq(prefix) + PSeq(token)
-    Assert(base0.take(len(base0) - 1) == base1)
-    Assert(base1.take(len(base1) - 1) == ToSeq(prefix))
-    # pk and secondary_action are ordinary (>= 0) segments, not DOTDOT (-1).
-    Assert(pk != DOTDOT())
-    Assert(secondary_action != DOTDOT())
-    # Unfold `resolve` one rel-step at a time (front-recursion), from the empty
-    # tail backwards, so each equality is a single definitional unfold.
-    Assert(resolve(ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action),
-                   rel.drop(1).drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix) + PSeq(pk), rel.drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix), rel.drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base1, rel.drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base0, rel)
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
+    result = [DOTDOT(), pk, secondary_action]  # type: List[int]
     return result
     # impl-end
```

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
                                             prefix[k] >= 0), [[prefix[k]]])))
     Requires(token >= 0 and current_action >= 0 and pk >= 0
              and secondary_action >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -104,37 +102,6 @@
     )
     # post-conditions-end
     # impl-start
-    # rel = ['..', '..', <pk>, <secondary_action>]
-    result = [DOTDOT(), DOTDOT(), pk, secondary_action]  # type: List[int]
-    # --- proof that resolving rel against the current location yields the
-    #     pk-keyed target (one unfold of `resolve` per step). ---
-    base0 = ToSeq(prefix) + PSeq(token) + PSeq(current_action)
-    rel = ToSeq(result)
-    # rel = [DOTDOT, DOTDOT, pk, secondary_action]
-    Assert(len(rel) == 4)
-    Assert(rel[0] == DOTDOT())
-    Assert(rel.drop(1)[0] == DOTDOT())
-    Assert(rel.drop(1).drop(1)[0] == pk)
-    Assert(rel.drop(1).drop(1).drop(1)[0] == secondary_action)
-    # base sequences after each pop / push, with the take/drop algebra facts.
-    base1 = ToSeq(prefix) + PSeq(token)
-    Assert(base0.take(len(base0) - 1) == base1)
-    Assert(base1.take(len(base1) - 1) == ToSeq(prefix))
-    # pk and secondary_action are ordinary (>= 0) segments, not DOTDOT (-1).
-    Assert(pk != DOTDOT())
-    Assert(secondary_action != DOTDOT())
-    # Unfold `resolve` one rel-step at a time (front-recursion), from the empty
-    # tail backwards, so each equality is a single definitional unfold.
-    Assert(resolve(ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action),
-                   rel.drop(1).drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix) + PSeq(pk), rel.drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix), rel.drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base1, rel.drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base0, rel)
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
+    result = [DOTDOT(), DOTDOT(), token, secondary_action]  # type: List[int]
     return result
     # impl-end
```

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
                                             prefix[k] >= 0), [[prefix[k]]])))
     Requires(token >= 0 and current_action >= 0 and pk >= 0
              and secondary_action >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -104,37 +102,7 @@
     )
     # post-conditions-end
     # impl-start
-    # rel = ['..', '..', <pk>, <secondary_action>]
-    result = [DOTDOT(), DOTDOT(), pk, secondary_action]  # type: List[int]
-    # --- proof that resolving rel against the current location yields the
-    #     pk-keyed target (one unfold of `resolve` per step). ---
-    base0 = ToSeq(prefix) + PSeq(token) + PSeq(current_action)
-    rel = ToSeq(result)
-    # rel = [DOTDOT, DOTDOT, pk, secondary_action]
-    Assert(len(rel) == 4)
-    Assert(rel[0] == DOTDOT())
-    Assert(rel.drop(1)[0] == DOTDOT())
-    Assert(rel.drop(1).drop(1)[0] == pk)
-    Assert(rel.drop(1).drop(1).drop(1)[0] == secondary_action)
-    # base sequences after each pop / push, with the take/drop algebra facts.
-    base1 = ToSeq(prefix) + PSeq(token)
-    Assert(base0.take(len(base0) - 1) == base1)
-    Assert(base1.take(len(base1) - 1) == ToSeq(prefix))
-    # pk and secondary_action are ordinary (>= 0) segments, not DOTDOT (-1).
-    Assert(pk != DOTDOT())
-    Assert(secondary_action != DOTDOT())
-    # Unfold `resolve` one rel-step at a time (front-recursion), from the empty
-    # tail backwards, so each equality is a single definitional unfold.
-    Assert(resolve(ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action),
-                   rel.drop(1).drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix) + PSeq(pk), rel.drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix), rel.drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base1, rel.drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base0, rel)
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
+    result = [DOTDOT(), DOTDOT(), pk, secondary_action,
+              secondary_action, DOTDOT()]  # type: List[int]
     return result
     # impl-end
```

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
                                             prefix[k] >= 0), [[prefix[k]]])))
     Requires(token >= 0 and current_action >= 0 and pk >= 0
              and secondary_action >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -104,37 +102,7 @@
     )
     # post-conditions-end
     # impl-start
-    # rel = ['..', '..', <pk>, <secondary_action>]
-    result = [DOTDOT(), DOTDOT(), pk, secondary_action]  # type: List[int]
-    # --- proof that resolving rel against the current location yields the
-    #     pk-keyed target (one unfold of `resolve` per step). ---
-    base0 = ToSeq(prefix) + PSeq(token) + PSeq(current_action)
-    rel = ToSeq(result)
-    # rel = [DOTDOT, DOTDOT, pk, secondary_action]
-    Assert(len(rel) == 4)
-    Assert(rel[0] == DOTDOT())
-    Assert(rel.drop(1)[0] == DOTDOT())
-    Assert(rel.drop(1).drop(1)[0] == pk)
-    Assert(rel.drop(1).drop(1).drop(1)[0] == secondary_action)
-    # base sequences after each pop / push, with the take/drop algebra facts.
-    base1 = ToSeq(prefix) + PSeq(token)
-    Assert(base0.take(len(base0) - 1) == base1)
-    Assert(base1.take(len(base1) - 1) == ToSeq(prefix))
-    # pk and secondary_action are ordinary (>= 0) segments, not DOTDOT (-1).
-    Assert(pk != DOTDOT())
-    Assert(secondary_action != DOTDOT())
-    # Unfold `resolve` one rel-step at a time (front-recursion), from the empty
-    # tail backwards, so each equality is a single definitional unfold.
-    Assert(resolve(ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action),
-                   rel.drop(1).drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix) + PSeq(pk), rel.drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix), rel.drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base1, rel.drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base0, rel)
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
+    result = [secondary_action, DOTDOT(), DOTDOT(), DOTDOT(),
+              pk, secondary_action]  # type: List[int]
     return result
     # impl-end
```

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
                                             prefix[k] >= 0), [[prefix[k]]])))
     Requires(token >= 0 and current_action >= 0 and pk >= 0
              and secondary_action >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -104,37 +102,7 @@
     )
     # post-conditions-end
     # impl-start
-    # rel = ['..', '..', <pk>, <secondary_action>]
-    result = [DOTDOT(), DOTDOT(), pk, secondary_action]  # type: List[int]
-    # --- proof that resolving rel against the current location yields the
-    #     pk-keyed target (one unfold of `resolve` per step). ---
-    base0 = ToSeq(prefix) + PSeq(token) + PSeq(current_action)
-    rel = ToSeq(result)
-    # rel = [DOTDOT, DOTDOT, pk, secondary_action]
-    Assert(len(rel) == 4)
-    Assert(rel[0] == DOTDOT())
-    Assert(rel.drop(1)[0] == DOTDOT())
-    Assert(rel.drop(1).drop(1)[0] == pk)
-    Assert(rel.drop(1).drop(1).drop(1)[0] == secondary_action)
-    # base sequences after each pop / push, with the take/drop algebra facts.
-    base1 = ToSeq(prefix) + PSeq(token)
-    Assert(base0.take(len(base0) - 1) == base1)
-    Assert(base1.take(len(base1) - 1) == ToSeq(prefix))
-    # pk and secondary_action are ordinary (>= 0) segments, not DOTDOT (-1).
-    Assert(pk != DOTDOT())
-    Assert(secondary_action != DOTDOT())
-    # Unfold `resolve` one rel-step at a time (front-recursion), from the empty
-    # tail backwards, so each equality is a single definitional unfold.
-    Assert(resolve(ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action),
-                   rel.drop(1).drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix) + PSeq(pk), rel.drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix), rel.drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base1, rel.drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base0, rel)
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
+    result = [DOTDOT(), DOTDOT(), DOTDOT(), DOTDOT(),
+              pk, secondary_action]  # type: List[int]
     return result
     # impl-end
```

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
                                             prefix[k] >= 0), [[prefix[k]]])))
     Requires(token >= 0 and current_action >= 0 and pk >= 0
              and secondary_action >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -104,37 +102,9 @@
     )
     # post-conditions-end
     # impl-start
-    # rel = ['..', '..', <pk>, <secondary_action>]
-    result = [DOTDOT(), DOTDOT(), pk, secondary_action]  # type: List[int]
-    # --- proof that resolving rel against the current location yields the
-    #     pk-keyed target (one unfold of `resolve` per step). ---
-    base0 = ToSeq(prefix) + PSeq(token) + PSeq(current_action)
-    rel = ToSeq(result)
-    # rel = [DOTDOT, DOTDOT, pk, secondary_action]
-    Assert(len(rel) == 4)
-    Assert(rel[0] == DOTDOT())
-    Assert(rel.drop(1)[0] == DOTDOT())
-    Assert(rel.drop(1).drop(1)[0] == pk)
-    Assert(rel.drop(1).drop(1).drop(1)[0] == secondary_action)
-    # base sequences after each pop / push, with the take/drop algebra facts.
-    base1 = ToSeq(prefix) + PSeq(token)
-    Assert(base0.take(len(base0) - 1) == base1)
-    Assert(base1.take(len(base1) - 1) == ToSeq(prefix))
-    # pk and secondary_action are ordinary (>= 0) segments, not DOTDOT (-1).
-    Assert(pk != DOTDOT())
-    Assert(secondary_action != DOTDOT())
-    # Unfold `resolve` one rel-step at a time (front-recursion), from the empty
-    # tail backwards, so each equality is a single definitional unfold.
-    Assert(resolve(ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action),
-                   rel.drop(1).drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix) + PSeq(pk), rel.drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix), rel.drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base1, rel.drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base0, rel)
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
+    if token >= 0:
+        result = [DOTDOT(), DOTDOT(), pk, secondary_action]  # type: List[int]
+    else:
+        result = [DOTDOT(), secondary_action]  # type: List[int]
     return result
     # impl-end
```

Attack 8 — `atk8.py` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
                                             prefix[k] >= 0), [[prefix[k]]])))
     Requires(token >= 0 and current_action >= 0 and pk >= 0
              and secondary_action >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -104,37 +102,7 @@
     )
     # post-conditions-end
     # impl-start
-    # rel = ['..', '..', <pk>, <secondary_action>]
-    result = [DOTDOT(), DOTDOT(), pk, secondary_action]  # type: List[int]
-    # --- proof that resolving rel against the current location yields the
-    #     pk-keyed target (one unfold of `resolve` per step). ---
-    base0 = ToSeq(prefix) + PSeq(token) + PSeq(current_action)
-    rel = ToSeq(result)
-    # rel = [DOTDOT, DOTDOT, pk, secondary_action]
-    Assert(len(rel) == 4)
-    Assert(rel[0] == DOTDOT())
-    Assert(rel.drop(1)[0] == DOTDOT())
-    Assert(rel.drop(1).drop(1)[0] == pk)
-    Assert(rel.drop(1).drop(1).drop(1)[0] == secondary_action)
-    # base sequences after each pop / push, with the take/drop algebra facts.
-    base1 = ToSeq(prefix) + PSeq(token)
-    Assert(base0.take(len(base0) - 1) == base1)
-    Assert(base1.take(len(base1) - 1) == ToSeq(prefix))
-    # pk and secondary_action are ordinary (>= 0) segments, not DOTDOT (-1).
-    Assert(pk != DOTDOT())
-    Assert(secondary_action != DOTDOT())
-    # Unfold `resolve` one rel-step at a time (front-recursion), from the empty
-    # tail backwards, so each equality is a single definitional unfold.
-    Assert(resolve(ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action),
-                   rel.drop(1).drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix) + PSeq(pk), rel.drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix), rel.drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base1, rel.drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base0, rel)
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
+    result = [DOTDOT(), DOTDOT(), pk, current_action,
+              DOTDOT(), secondary_action]  # type: List[int]
     return result
     # impl-end
```

Attack 9 — `atk9.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
                                             prefix[k] >= 0), [[prefix[k]]])))
     Requires(token >= 0 and current_action >= 0 and pk >= 0
              and secondary_action >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -104,37 +102,42 @@
     )
     # post-conditions-end
     # impl-start
-    # rel = ['..', '..', <pk>, <secondary_action>]
-    result = [DOTDOT(), DOTDOT(), pk, secondary_action]  # type: List[int]
-    # --- proof that resolving rel against the current location yields the
-    #     pk-keyed target (one unfold of `resolve` per step). ---
+    result = [DOTDOT(), DOTDOT(), pk, secondary_action,
+              secondary_action, DOTDOT()]  # type: List[int]
     base0 = ToSeq(prefix) + PSeq(token) + PSeq(current_action)
     rel = ToSeq(result)
-    # rel = [DOTDOT, DOTDOT, pk, secondary_action]
-    Assert(len(rel) == 4)
+    Assert(len(rel) == 6)
     Assert(rel[0] == DOTDOT())
     Assert(rel.drop(1)[0] == DOTDOT())
     Assert(rel.drop(1).drop(1)[0] == pk)
     Assert(rel.drop(1).drop(1).drop(1)[0] == secondary_action)
-    # base sequences after each pop / push, with the take/drop algebra facts.
+    Assert(rel.drop(1).drop(1).drop(1).drop(1)[0] == secondary_action)
+    Assert(rel.drop(1).drop(1).drop(1).drop(1).drop(1)[0] == DOTDOT())
     base1 = ToSeq(prefix) + PSeq(token)
     Assert(base0.take(len(base0) - 1) == base1)
     Assert(base1.take(len(base1) - 1) == ToSeq(prefix))
-    # pk and secondary_action are ordinary (>= 0) segments, not DOTDOT (-1).
     Assert(pk != DOTDOT())
     Assert(secondary_action != DOTDOT())
-    # Unfold `resolve` one rel-step at a time (front-recursion), from the empty
-    # tail backwards, so each equality is a single definitional unfold.
+    # unfold from the empty tail backwards
+    target = ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action)
+    # after both '..': base == prefix ; then push pk, push sa, push sa, pop sa
+    tps = ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action) + PSeq(secondary_action)
+    Assert(tps.take(len(tps) - 1) == target)
+    Assert(resolve(target, rel.drop(1).drop(1).drop(1).drop(1).drop(1).drop(1))
+           == target)
+    # step: DOTDOT on tps -> target
+    Assert(resolve(tps, rel.drop(1).drop(1).drop(1).drop(1).drop(1)) == target)
+    # step: push sa onto (prefix+pk+sa) -> tps
     Assert(resolve(ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action),
-                   rel.drop(1).drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix) + PSeq(pk), rel.drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix), rel.drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base1, rel.drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base0, rel)
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
+                   rel.drop(1).drop(1).drop(1).drop(1)) == target)
+    # step: push sa onto (prefix+pk) -> prefix+pk+sa
+    Assert(resolve(ToSeq(prefix) + PSeq(pk),
+                   rel.drop(1).drop(1).drop(1)) == target)
+    # step: push pk onto prefix -> prefix+pk
+    Assert(resolve(ToSeq(prefix), rel.drop(1).drop(1)) == target)
+    # step: DOTDOT on base1 -> prefix
+    Assert(resolve(base1, rel.drop(1)) == target)
+    # step: DOTDOT on base0 -> base1
+    Assert(resolve(base0, rel) == target)
     return result
     # impl-end
```

Attack 10 — `atk10.py` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -40,7 +40,6 @@
 """
 from typing import List
 from nagini_contracts.contracts import *
-from nagini_contracts.obligations import MustTerminate
 
 
 # axioms-start
@@ -89,7 +88,6 @@
                                             prefix[k] >= 0), [[prefix[k]]])))
     Requires(token >= 0 and current_action >= 0 and pk >= 0
              and secondary_action >= 0)
-    Requires(MustTerminate(2))
     # pre-conditions-end
     # post-conditions-start
     Ensures(Acc(list_pred(prefix), 1 / 2))
@@ -104,37 +102,36 @@
     )
     # post-conditions-end
     # impl-start
-    # rel = ['..', '..', <pk>, <secondary_action>]
-    result = [DOTDOT(), DOTDOT(), pk, secondary_action]  # type: List[int]
-    # --- proof that resolving rel against the current location yields the
-    #     pk-keyed target (one unfold of `resolve` per step). ---
+    result = [DOTDOT(), DOTDOT(), pk, current_action,
+              DOTDOT(), secondary_action]  # type: List[int]
     base0 = ToSeq(prefix) + PSeq(token) + PSeq(current_action)
     rel = ToSeq(result)
-    # rel = [DOTDOT, DOTDOT, pk, secondary_action]
-    Assert(len(rel) == 4)
+    Assert(len(rel) == 6)
     Assert(rel[0] == DOTDOT())
     Assert(rel.drop(1)[0] == DOTDOT())
     Assert(rel.drop(1).drop(1)[0] == pk)
-    Assert(rel.drop(1).drop(1).drop(1)[0] == secondary_action)
-    # base sequences after each pop / push, with the take/drop algebra facts.
+    Assert(rel.drop(1).drop(1).drop(1)[0] == current_action)
+    Assert(rel.drop(1).drop(1).drop(1).drop(1)[0] == DOTDOT())
+    Assert(rel.drop(1).drop(1).drop(1).drop(1).drop(1)[0] == secondary_action)
     base1 = ToSeq(prefix) + PSeq(token)
     Assert(base0.take(len(base0) - 1) == base1)
     Assert(base1.take(len(base1) - 1) == ToSeq(prefix))
-    # pk and secondary_action are ordinary (>= 0) segments, not DOTDOT (-1).
     Assert(pk != DOTDOT())
+    Assert(current_action != DOTDOT())
     Assert(secondary_action != DOTDOT())
-    # Unfold `resolve` one rel-step at a time (front-recursion), from the empty
-    # tail backwards, so each equality is a single definitional unfold.
-    Assert(resolve(ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action),
-                   rel.drop(1).drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix) + PSeq(pk), rel.drop(1).drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(ToSeq(prefix), rel.drop(1).drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base1, rel.drop(1))
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
-    Assert(resolve(base0, rel)
-           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
+    target = ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action)
+    ppc = ToSeq(prefix) + PSeq(pk) + PSeq(current_action)
+    Assert(ppc.take(len(ppc) - 1) == ToSeq(prefix) + PSeq(pk))
+    Assert(resolve(target, rel.drop(1).drop(1).drop(1).drop(1).drop(1).drop(1)) == target)
+    # push sa onto (prefix+pk) -> target
+    Assert(resolve(ToSeq(prefix) + PSeq(pk), rel.drop(1).drop(1).drop(1).drop(1).drop(1)) == target)
+    # DOTDOT on ppc -> prefix+pk
+    Assert(resolve(ppc, rel.drop(1).drop(1).drop(1).drop(1)) == target)
+    # push current_action onto (prefix+pk) -> ppc
+    Assert(resolve(ToSeq(prefix) + PSeq(pk), rel.drop(1).drop(1).drop(1)) == target)
+    # push pk onto prefix -> prefix+pk
+    Assert(resolve(ToSeq(prefix), rel.drop(1).drop(1)) == target)
+    Assert(resolve(base1, rel.drop(1)) == target)
+    Assert(resolve(base0, rel) == target)
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16139.

Behaviour under specification (stated as desired behaviour):

  When an editable object is reachable through more than one identifier, a
  read-only field offers a relative hyperlink to a SECONDARY action page for
  that same object. The action page is addressed by the object's CANONICAL
  identifier (its primary key), NOT by whatever identifier happened to be used
  to reach the current page. So the relative reference, once resolved against
  the current page's location, must land on the action page keyed by the
  canonical identifier, regardless of which identifier addressed the current
  page.

  Concretely: the current page lives at a location whose path is

      [.. shared prefix ..] / <access-token> / <current-action>         (a "directory" URL, trailing slash)

  and the desired target is

      [.. shared prefix ..] / <primary-key> / <secondary-action>

  The function builds a RELATIVE reference `rel` (a list of path steps, each
  either an ordinary segment or the up-one-level step "..") to embed in the
  page. Correctness means: resolving `rel` against the current location yields
  exactly the target above, for EVERY access-token value — in particular when
  the access-token differs from the primary key.

Relative-reference resolution is the standard hierarchical-URL rule (pop one
segment per ".."; otherwise append). It is modelled DEEPLY here as a verified
segment fold (`resolve`), validated equal to the real resolver out of band by
axiom_check.py (G-AX), NOT consumed as an axiom.

URLs are modelled as `List[int]` / `PSeq[int]` of opaque path-segment ids; the
sentinel `DOTDOT == -1` denotes the up-one-level step. Distinct ids model
distinct path segments (so an access-token id and a primary-key id are
independent), which is exactly what lets the spec require the resolved target
to be keyed by the primary key for every access-token value.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axioms. The one unchanged callee whose semantics
#  the proof relies on — hierarchical relative-reference resolution — is
#  modelled DEEPLY as the verified pure fold `resolve` below, and validated
#  equal to the real resolver by axiom_check.py / G-AX as an A-reference.)
# axioms-end


# pure-start
@Pure
def DOTDOT() -> int:
    """Sentinel path step meaning 'up one level' (the ".." segment)."""
    return -1


@Pure
def resolve(base_dir: PSeq[int], rel: PSeq[int]) -> PSeq[int]:
    """Resolve a relative reference `rel` against the directory-segment list
    `base_dir` of the current (trailing-slash) location, per the standard
    hierarchical rule: a ".." step (DOTDOT) drops the last accumulated segment;
    any other step is appended. Front-recursive over `rel` so a single unfold
    is available per loop step."""
    if len(rel) == 0:
        return base_dir
    if rel[0] == DOTDOT():
        if len(base_dir) == 0:
            return resolve(base_dir, rel.drop(1))
        return resolve(base_dir.take(len(base_dir) - 1), rel.drop(1))
    return resolve(base_dir + PSeq(rel[0]), rel.drop(1))
# pure-end


def build_action_reference(prefix: List[int], token: int, current_action: int,
                           pk: int, secondary_action: int) -> List[int]:
    # pre-conditions-start
    # `prefix` is the constant, shared leading path of both URLs (e.g. the
    # collection path up to but excluding the per-object identifier). It is
    # read, never mutated -> fractional permission, required AND ensured.
    Requires(Acc(list_pred(prefix), 1 / 2))
    # The up-one-level sentinel must not collide with any real segment id used
    # in the location: ordinary segments (prefix entries, token, action codes,
    # pk) are non-negative; DOTDOT is the only negative step.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(prefix),
                                            prefix[k] >= 0), [[prefix[k]]])))
    Requires(token >= 0 and current_action >= 0 and pk >= 0
             and secondary_action >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(prefix), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Resolving the produced relative reference against the current location
    # lands EXACTLY on the secondary-action page keyed by the PRIMARY KEY,
    # for every access token (the token is popped away, the pk is supplied).
    Ensures(
        resolve(ToSeq(prefix) + PSeq(token) + PSeq(current_action),
                ToSeq(Result()))
        == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action)
    )
    # post-conditions-end
    # impl-start
    # rel = ['..', '..', <pk>, <secondary_action>]
    result = [DOTDOT(), DOTDOT(), pk, secondary_action]  # type: List[int]
    # --- proof that resolving rel against the current location yields the
    #     pk-keyed target (one unfold of `resolve` per step). ---
    base0 = ToSeq(prefix) + PSeq(token) + PSeq(current_action)
    rel = ToSeq(result)
    # rel = [DOTDOT, DOTDOT, pk, secondary_action]
    Assert(len(rel) == 4)
    Assert(rel[0] == DOTDOT())
    Assert(rel.drop(1)[0] == DOTDOT())
    Assert(rel.drop(1).drop(1)[0] == pk)
    Assert(rel.drop(1).drop(1).drop(1)[0] == secondary_action)
    # base sequences after each pop / push, with the take/drop algebra facts.
    base1 = ToSeq(prefix) + PSeq(token)
    Assert(base0.take(len(base0) - 1) == base1)
    Assert(base1.take(len(base1) - 1) == ToSeq(prefix))
    # pk and secondary_action are ordinary (>= 0) segments, not DOTDOT (-1).
    Assert(pk != DOTDOT())
    Assert(secondary_action != DOTDOT())
    # Unfold `resolve` one rel-step at a time (front-recursion), from the empty
    # tail backwards, so each equality is a single definitional unfold.
    Assert(resolve(ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action),
                   rel.drop(1).drop(1).drop(1).drop(1))
           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
    Assert(resolve(ToSeq(prefix) + PSeq(pk), rel.drop(1).drop(1).drop(1))
           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
    Assert(resolve(ToSeq(prefix), rel.drop(1).drop(1))
           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
    Assert(resolve(base1, rel.drop(1))
           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
    Assert(resolve(base0, rel)
           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS SOUND under adversarial G-EQ (refinement fidelity). 12 same-spec impls run (all same-spec exit 0). No verifying wrong impl exists whose faithful patch fails to resolve.

SPEC SHAPE: postcondition resolve(ToSeq(prefix)+PSeq(token)+PSeq(current_action), ToSeq(Result())) == ToSeq(prefix)+PSeq(pk)+PSeq(secondary_action), universally quantified over ALL prefix (List[int], any length incl. empty), token, current_action, pk, secondary_action (all >=0). No consumed @ContractOnly axiom; single A-reference: deep model `resolve` == urllib.parse.urljoin.

WHY SOUND (key argument): the postcondition quantifies over ALL prefix including the empty and arbitrarily-deep prefix. This forces any verifying reference to pop EXACTLY the current-action and token segments and never below the prefix boundary — i.e. it constrains the impl to the non-over-popping domain where resolve == urljoin PROVABLY holds (G-AX). Over-popping refs (atk6) give wrong results on deep prefixes and are rejected. Thus every verifying impl yields a reference that resolves identically under the REAL resolver. Confirmed the F2P test (tests/auth_tests/test_forms.py::test_link_to_password_reset_in_helptext_via_to_field) compares via urllib.parse.urljoin(admin_user_change_url, href) == pw_change_url — a SEMANTIC (resolved) comparison, NOT a raw-string match — so any urljoin-equivalent reference resolves. This matches the deep model exactly.

### ATTACKS (all same-spec exit 0):
- atk1 (prepatch bug [DOTDOT,sa] = '../password/', token-keyed): weakness -> NOT-A-COUNTEREXAMPLE (does not verify). Prepatch reproduced.
- atk2 (single-pop [DOTDOT,pk,sa]): does not verify.
- atk3 (token-keyed [DOTDOT,DOTDOT,token,sa]): does not verify.
- atk4 (bare echo [DOTDOT,DOTDOT,pk,sa,sa,DOTDOT] w/o proof): does not verify (missing proof scaffold).
- atk5 (bare echo leading no-op): does not verify.
- atk6 (over-pop [DOTDOT,DOTDOT,DOTDOT,DOTDOT,pk,sa]): does not verify (wrong on deep prefix; boundary attack).
- atk7 (control-flow-effect: if token>=0 gold else prepatch): does not verify (else branch violates post).
- atk8 (bare echo mid no-op): does not verify.
- atk9 (PROVED echo [DOTDOT,DOTDOT,pk,sa,sa,DOTDOT] with full unfold proof): weakness -> CANDIDATE (shares spec AND verifies, 12.0s). Materialized faithful patch (f"../../{pk}/password/password/../") -> run_resolve RESOLVED=True, COMPLETED=True (F2P success, all PASS_TO_PASS success). NOT a break.
- atk10 (PROVED echo [DOTDOT,DOTDOT,pk,current_action,DOTDOT,sa] with full proof): weakness -> CANDIDATE (verifies, 13.1s). Materialized faithful patch (f"../../{pk}/change/../password/") -> run_resolve: first attempt COMPLETED=False (no-report infra flake), retry RESOLVED=True COMPLETED=True (F2P success). NOT a break.

### COMMANDS (SBU_BENCHMARK_DIR=benchmark-verified):
  python -m swebench_unified.adversary same-spec nagini django__django-16139 <atk>  (all exit 0)
  python -m swebench_unified.adversary weakness nagini django__django-16139 <atk>   (atk1-8 exit 2; atk9,atk10 exit 0 CANDIDATE)
  bash scripts/nagini_verify.sh pos_control.py -> Verification successful (12.18s, exit 0)
  run_resolve('django__django-16139', patch_atk9)  -> resolved=True
  run_resolve('django__django-16139', patch_atk10) -> resolved=True (after 1 infra-flake retry)

POSITIVE CONTROL: gold model.py verifies (nagini_verify.sh exit 0, 12.18s).

REFINEMENT.MD AUDIT (A-legs): meta.json axioms == [] (no consumed axiom). Legs A1 (params, R), A2 (result list == f-string, R+I), A3 (.format/markup, R identity), A4 (resolution clause, A-reference). No kind-3 (unexpressible-changed-op) step: the one changed-result op (the reference) is modeled directly as A2 (R+I); the unchanged callee (urljoin) is a DEEP MODEL (A-reference), not a hidden consumed axiom. A-reference correspondence VERIFIED: axiom_check.py run -> 'G-AX OK: resolve deep model (== urllib.parse.urljoin) sound on 35 boundary + 20000 fuzz inputs; 5000 token/pk witnesses' (exit 0). The deep model's declared non-over-popping domain is exactly the domain any verifying impl is confined to (see soundness argument), so the A-reference restriction is sound, not an escape hatch.

CONCLUSION: no verifying wrong impl exists whose faithful refined patch fails run_resolve; both proved verifying CANDIDATEs (atk9,atk10) resolve; prepatch reproduced; positive control verifies; A-reference sound; no kind-3 legs. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk1.py`, `atk2.py`, `atk3.py`, `atk4.py`, `atk5.py`, `atk6.py`, `atk7.py`, `atk8.py` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk9.py`, `atk10.py` |

**Non-vacuity.** The positive control `pos_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.py` → rejected (same spec, does not verify — good)

Attack 8 — `atk8.py` → rejected (same spec, does not verify — good)

Attack 9 — `atk9.py` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk10.py` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.py`

```python
"""Twin-artifact model for django__django-16139.

Behaviour under specification (stated as desired behaviour):

  When an editable object is reachable through more than one identifier, a
  read-only field offers a relative hyperlink to a SECONDARY action page for
  that same object. The action page is addressed by the object's CANONICAL
  identifier (its primary key), NOT by whatever identifier happened to be used
  to reach the current page. So the relative reference, once resolved against
  the current page's location, must land on the action page keyed by the
  canonical identifier, regardless of which identifier addressed the current
  page.

  Concretely: the current page lives at a location whose path is

      [.. shared prefix ..] / <access-token> / <current-action>         (a "directory" URL, trailing slash)

  and the desired target is

      [.. shared prefix ..] / <primary-key> / <secondary-action>

  The function builds a RELATIVE reference `rel` (a list of path steps, each
  either an ordinary segment or the up-one-level step "..") to embed in the
  page. Correctness means: resolving `rel` against the current location yields
  exactly the target above, for EVERY access-token value — in particular when
  the access-token differs from the primary key.

Relative-reference resolution is the standard hierarchical-URL rule (pop one
segment per ".."; otherwise append). It is modelled DEEPLY here as a verified
segment fold (`resolve`), validated equal to the real resolver out of band by
axiom_check.py (G-AX), NOT consumed as an axiom.

URLs are modelled as `List[int]` / `PSeq[int]` of opaque path-segment ids; the
sentinel `DOTDOT == -1` denotes the up-one-level step. Distinct ids model
distinct path segments (so an access-token id and a primary-key id are
independent), which is exactly what lets the spec require the resolved target
to be keyed by the primary key for every access-token value.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed @ContractOnly axioms. The one unchanged callee whose semantics
#  the proof relies on — hierarchical relative-reference resolution — is
#  modelled DEEPLY as the verified pure fold `resolve` below, and validated
#  equal to the real resolver by axiom_check.py / G-AX as an A-reference.)
# axioms-end


# pure-start
@Pure
def DOTDOT() -> int:
    """Sentinel path step meaning 'up one level' (the ".." segment)."""
    return -1


@Pure
def resolve(base_dir: PSeq[int], rel: PSeq[int]) -> PSeq[int]:
    """Resolve a relative reference `rel` against the directory-segment list
    `base_dir` of the current (trailing-slash) location, per the standard
    hierarchical rule: a ".." step (DOTDOT) drops the last accumulated segment;
    any other step is appended. Front-recursive over `rel` so a single unfold
    is available per loop step."""
    if len(rel) == 0:
        return base_dir
    if rel[0] == DOTDOT():
        if len(base_dir) == 0:
            return resolve(base_dir, rel.drop(1))
        return resolve(base_dir.take(len(base_dir) - 1), rel.drop(1))
    return resolve(base_dir + PSeq(rel[0]), rel.drop(1))
# pure-end


def build_action_reference(prefix: List[int], token: int, current_action: int,
                           pk: int, secondary_action: int) -> List[int]:
    # pre-conditions-start
    # `prefix` is the constant, shared leading path of both URLs (e.g. the
    # collection path up to but excluding the per-object identifier). It is
    # read, never mutated -> fractional permission, required AND ensured.
    Requires(Acc(list_pred(prefix), 1 / 2))
    # The up-one-level sentinel must not collide with any real segment id used
    # in the location: ordinary segments (prefix entries, token, action codes,
    # pk) are non-negative; DOTDOT is the only negative step.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(prefix),
                                            prefix[k] >= 0), [[prefix[k]]])))
    Requires(token >= 0 and current_action >= 0 and pk >= 0
             and secondary_action >= 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(prefix), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Resolving the produced relative reference against the current location
    # lands EXACTLY on the secondary-action page keyed by the PRIMARY KEY,
    # for every access token (the token is popped away, the pk is supplied).
    Ensures(
        resolve(ToSeq(prefix) + PSeq(token) + PSeq(current_action),
                ToSeq(Result()))
        == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action)
    )
    # post-conditions-end
    # impl-start
    # rel = ['..', '..', <pk>, <secondary_action>]
    result = [DOTDOT(), DOTDOT(), pk, secondary_action]  # type: List[int]
    # --- proof that resolving rel against the current location yields the
    #     pk-keyed target (one unfold of `resolve` per step). ---
    base0 = ToSeq(prefix) + PSeq(token) + PSeq(current_action)
    rel = ToSeq(result)
    # rel = [DOTDOT, DOTDOT, pk, secondary_action]
    Assert(len(rel) == 4)
    Assert(rel[0] == DOTDOT())
    Assert(rel.drop(1)[0] == DOTDOT())
    Assert(rel.drop(1).drop(1)[0] == pk)
    Assert(rel.drop(1).drop(1).drop(1)[0] == secondary_action)
    # base sequences after each pop / push, with the take/drop algebra facts.
    base1 = ToSeq(prefix) + PSeq(token)
    Assert(base0.take(len(base0) - 1) == base1)
    Assert(base1.take(len(base1) - 1) == ToSeq(prefix))
    # pk and secondary_action are ordinary (>= 0) segments, not DOTDOT (-1).
    Assert(pk != DOTDOT())
    Assert(secondary_action != DOTDOT())
    # Unfold `resolve` one rel-step at a time (front-recursion), from the empty
    # tail backwards, so each equality is a single definitional unfold.
    Assert(resolve(ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action),
                   rel.drop(1).drop(1).drop(1).drop(1))
           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
    Assert(resolve(ToSeq(prefix) + PSeq(pk), rel.drop(1).drop(1).drop(1))
           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
    Assert(resolve(ToSeq(prefix), rel.drop(1).drop(1))
           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
    Assert(resolve(base1, rel.drop(1))
           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
    Assert(resolve(base0, rel)
           == ToSeq(prefix) + PSeq(pk) + PSeq(secondary_action))
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS SOUND under adversarial G-EQ (refinement fidelity). 12 same-spec impls run (all same-spec exit 0). No verifying wrong impl exists whose faithful patch fails to resolve.

SPEC SHAPE: postcondition resolve(ToSeq(prefix)+PSeq(token)+PSeq(current_action), ToSeq(Result())) == ToSeq(prefix)+PSeq(pk)+PSeq(secondary_action), universally quantified over ALL prefix (List[int], any length incl. empty), token, current_action, pk, secondary_action (all >=0). No consumed @ContractOnly axiom; single A-reference: deep model `resolve` == urllib.parse.urljoin.

WHY SOUND (key argument): the postcondition quantifies over ALL prefix including the empty and arbitrarily-deep prefix. This forces any verifying reference to pop EXACTLY the current-action and token segments and never below the prefix boundary — i.e. it constrains the impl to the non-over-popping domain where resolve == urljoin PROVABLY holds (G-AX). Over-popping refs (atk6) give wrong results on deep prefixes and are rejected. Thus every verifying impl yields a reference that resolves identically under the REAL resolver. Confirmed the F2P test (tests/auth_tests/test_forms.py::test_link_to_password_reset_in_helptext_via_to_field) compares via urllib.parse.urljoin(admin_user_change_url, href) == pw_change_url — a SEMANTIC (resolved) comparison, NOT a raw-string match — so any urljoin-equivalent reference resolves. This matches the deep model exactly.

### ATTACKS (all same-spec exit 0):
- atk1 (prepatch bug [DOTDOT,sa] = '../password/', token-keyed): weakness -> NOT-A-COUNTEREXAMPLE (does not verify). Prepatch reproduced.
- atk2 (single-pop [DOTDOT,pk,sa]): does not verify.
- atk3 (token-keyed [DOTDOT,DOTDOT,token,sa]): does not verify.
- atk4 (bare echo [DOTDOT,DOTDOT,pk,sa,sa,DOTDOT] w/o proof): does not verify (missing proof scaffold).
- atk5 (bare echo leading no-op): does not verify.
- atk6 (over-pop [DOTDOT,DOTDOT,DOTDOT,DOTDOT,pk,sa]): does not verify (wrong on deep prefix; boundary attack).
- atk7 (control-flow-effect: if token>=0 gold else prepatch): does not verify (else branch violates post).
- atk8 (bare echo mid no-op): does not verify.
- atk9 (PROVED echo [DOTDOT,DOTDOT,pk,sa,sa,DOTDOT] with full unfold proof): weakness -> CANDIDATE (shares spec AND verifies, 12.0s). Materialized faithful patch (f"../../{pk}/password/password/../") -> run_resolve RESOLVED=True, COMPLETED=True (F2P success, all PASS_TO_PASS success). NOT a break.
- atk10 (PROVED echo [DOTDOT,DOTDOT,pk,current_action,DOTDOT,sa] with full proof): weakness -> CANDIDATE (verifies, 13.1s). Materialized faithful patch (f"../../{pk}/change/../password/") -> run_resolve: first attempt COMPLETED=False (no-report infra flake), retry RESOLVED=True COMPLETED=True (F2P success). NOT a break.

### COMMANDS (SBU_BENCHMARK_DIR=benchmark-verified):
  python -m swebench_unified.adversary same-spec nagini django__django-16139 <atk>  (all exit 0)
  python -m swebench_unified.adversary weakness nagini django__django-16139 <atk>   (atk1-8 exit 2; atk9,atk10 exit 0 CANDIDATE)
  bash scripts/nagini_verify.sh pos_control.py -> Verification successful (12.18s, exit 0)
  run_resolve('django__django-16139', patch_atk9)  -> resolved=True
  run_resolve('django__django-16139', patch_atk10) -> resolved=True (after 1 infra-flake retry)

POSITIVE CONTROL: gold model.py verifies (nagini_verify.sh exit 0, 12.18s).

REFINEMENT.MD AUDIT (A-legs): meta.json axioms == [] (no consumed axiom). Legs A1 (params, R), A2 (result list == f-string, R+I), A3 (.format/markup, R identity), A4 (resolution clause, A-reference). No kind-3 (unexpressible-changed-op) step: the one changed-result op (the reference) is modeled directly as A2 (R+I); the unchanged callee (urljoin) is a DEEP MODEL (A-reference), not a hidden consumed axiom. A-reference correspondence VERIFIED: axiom_check.py run -> 'G-AX OK: resolve deep model (== urllib.parse.urljoin) sound on 35 boundary + 20000 fuzz inputs; 5000 token/pk witnesses' (exit 0). The deep model's declared non-over-popping domain is exactly the domain any verifying impl is confined to (see soundness argument), so the A-reference restriction is sound, not an escape hatch.

CONCLUSION: no verifying wrong impl exists whose faithful refined patch fails run_resolve; both proved verifying CANDIDATEs (atk9,atk10) resolve; prepatch reproduced; positive control verifies; A-reference sound; no kind-3 legs. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of django__django-16139 nagini bundle. No in-domain input found where the modeled function/spec disagrees with the real callee.

Setup verified: (1) same-spec exit 0 — model.py shares the bundle's exact byte-identical spec regions (docstring, pure/resolve deep model, pre/postconditions). (2) Nagini verifies model.py in ~12.25s (exit 0), so the postcondition is satisfiable by the gold impl — the spec is not over-strong-to-unsatisfiability. (3) G-CONF (conformance_check.py) passed on 100040 inputs against the REAL patched UserChangeForm (recorded in meta.json), diffing the shadow impl's rendered href against the real form's help-text href AND the urljoin-resolved targets — zero disagreements.

The faithfulness risk is the deep-model reference `resolve` vs the real callee `urllib.parse.urljoin`. I ran an INDEPENDENT differential fuzz over the modeled precondition domain (prefix any non-negative segment ids, base = prefix+[token,current_action], all of token/current_action/pk/secondary_action >= 0, gold rel = [DOTDOT,DOTDOT,pk,sa]): 500,000 randomized cases + targeted edge probes on the tightest 2-pop-to-root boundary (empty prefix, base depth exactly 2). In every case: resolve == urllib.parse.urljoin AND resolve(base, rel) == the spec target prefix+[pk,sa]. Zero mismatches.

Two declared divergence risks examined and confirmed to be honest, sound domain restrictions rather than hidden over-strength: (a) Root over-pop when base depth < number of '..' pops — excluded because token,current_action >= 0 keep base depth >= 2, so the two '..' pops land exactly at `prefix`; deeper over-pop is declared out-of-domain and unreachable (admin URLs have depth >= 5). axiom_check.py's overpops_root() correctly restricts validation to this domain. (b) A to_field access token that is itself a literal dot-segment ('..'/'.') would make real urljoin diverge from resolve (which treats token as an opaque non-DOTDOT segment); the precondition token >= 0 (DOTDOT == -1 is the only special id) excludes exactly this, and it lies outside the F2P test's inputs. Neither is an in-precondition diverging input.

The modeled build_action_reference maps to UserChangeForm.__init__'s reference build (django/contrib/auth/forms.py:166): gold produces f"../../{pk}/password/" == model's [DOTDOT,DOTDOT,pk,secondary_action], resolving against the token-keyed change URL to the pk-keyed password page for every token — matching real urljoin. Spec is faithful; no in-domain diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> hard_failures=[]) and semantic review agrees. The public problem_statement already discloses the ENTIRE gold edit verbatim ('replacing password.help_text.format("../password/") with password.help_text.format(f"../../{self.instance.pk}/password/")') plus the full to_field/pk-keyed diagnosis, so the leakage bar is measured against a maximally-informative task text. The spec view is strictly MORE abstract than that: the impl region is elided ('... implementation elided — supplied by the consumer'), so the gold construction [DOTDOT(), DOTDOT(), pk, secondary_action] is hidden; no concrete strings ('../password/', '../../{pk}/password/'), no patched symbols (UserChangeForm, help_text, password, ReadOnlyPasswordHashField), no patched file path (django/contrib/auth/forms.py), no diff markers, and no bug/fix narration appear. The spec is phrased over opaque List[int]/PSeq[int] path-segment ids with a DOTDOT sentinel and a deep 'resolve' fold, and the postcondition (resolve(prefix+[token]+[current_action], rel) == prefix+[pk]+[secondary_action] for every token) encodes only the desired behavior already stated publicly. No spec-view line reveals the gold edit beyond the public problem_statement (hints_text not consulted). Byte-identical spec confirmed via the same-spec toolkit path (leak screen operates over the projected spec_view).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
